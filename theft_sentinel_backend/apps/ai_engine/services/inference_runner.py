"""
Inference Runner — per-camera frame processor.

Each ContinuousMonitor (or on-demand view) owns one InferenceRunner instance.
The instance holds its own DeepSORT tracker and embedding-smoothing buffer so
that per-camera state is completely isolated between threads.

All GPU calls and shared-state mutations go through the locks on AIService:
  ai_service.inference_lock  — GPU forward passes (YOLO / OSNet / X3D)
  ai_service.state_lock      — FAISS index, ClipBuffer, theft_scores,
                               x3d_frame_counters

Public method signatures (preserved for backward compatibility with views.py):
  run_inference(frame_bgr, camera_id=None) -> dict
  process_frame(frame_bgr, camera_id=None) -> dict  ← alias, keeps views working
  reset()

Return dict keys (unchanged API contract):
  classification      "theft" | "normal"
  confidence          float 0–1
  detections          list  YOLO boxes  {bbox, confidence, class, class_id}
  poses               []    always empty (no pose model in new pipeline)
  tracks              list  DeepSORT tracks with global_id injected
  suspicious_tracks   list  tracks whose latest X3D score ≥ SUSPICIOUS_THRESHOLD
  frame_metadata      dict  (includes raw_x3d_score; suspicious=True when ≥ 0.50)
  processing_time_ms  float

Threshold behaviour (clarification #1):
  score ≥ X3D_THEFT_THRESHOLD (0.80)      → classification="theft", alert eligible
  score ≥ X3D_SUSPICIOUS_THRESHOLD (0.50) → classification="normal",
                                             frame_metadata["suspicious"] = True
  score <  X3D_SUSPICIOUS_THRESHOLD       → classification="normal"
  raw_x3d_score is always included in frame_metadata regardless of threshold.
"""

import collections
import threading
import time
from typing import Any, Dict, List, Optional

import numpy as np
import logging

logger = logging.getLogger(__name__)

from .ai_service import ai_service

# Pipeline constants — imported directly from ai_pipeline config, never
# re-declared here (per clarification requirement).
from ai_pipeline.ai_config.config import Config

# Per-camera tracker — one instance per InferenceRunner, never shared.
from ai_pipeline.tracking.tracker import MultiObjectTracker


# ── module-level integer camera ID counter ────────────────────────────────────
# Each InferenceRunner gets a unique small integer as the internal camera ID
# used for DeepSORT and the FAISS/DB identity system.  The string MongoDB
# camera_id is only used for metadata, never for the pipeline internals.
_cam_counter_lock = threading.Lock()
_cam_counter: int = 0


def _next_int_camera_id() -> int:
    global _cam_counter
    with _cam_counter_lock:
        _cam_counter += 1
        return _cam_counter


def _bbox_iou(b1: List[float], b2: List[float]) -> float:
    """Intersection-over-Union for two [x1,y1,x2,y2] boxes."""
    x1 = max(b1[0], b2[0]);  y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2]);  y2 = min(b1[3], b2[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0


class InferenceRunner:
    """
    Stateful per-camera pipeline runner.

    Maintains:
      • A DeepSORT tracker (thread-isolated — no sharing)
      • A per-(cam_id, track_id) embedding smoothing deque (maxlen=10)
      • Per-(cam_id, track_id) embedding update counters
      • A local frame counter for periodic maintenance scheduling

    All GPU calls and shared-state writes use the locks from AIService.
    """

    # How often to prune expired global IDs (frames processed)
    _PRUNE_EVERY   = 300
    # How often to rebuild FAISS from DB (frames processed)
    _REBUILD_EVERY = 500

    def __init__(self) -> None:
        # Unique integer camera ID for the internal pipeline
        self._int_cam_id: int = _next_int_camera_id()

        # Lazy-initialised tracker (avoids import-time MultiObjectTracker
        # construction before AIService.initialize() has set Config.DEVICE).
        self._tracker: Optional[MultiObjectTracker] = None

        # Per-track embedding smoothing: (int_cam_id, track_id) → deque
        self._embed_buf:        Dict[tuple, collections.deque] = {}
        # Per-track counter to throttle DB / FAISS embedding updates
        self._embed_update_cnt: Dict[tuple, int]               = {}

        self._frame_idx: int = 0

    # ── internal helpers ──────────────────────────────────────────────────────

    def _ensure_tracker(self) -> None:
        """Lazily create the DeepSORT tracker on first use."""
        if self._tracker is None:
            self._tracker = MultiObjectTracker(self._int_cam_id)

    def _match_det_to_track(
        self,
        track_bbox: List[float],
        raw_dets:   List[Dict],
    ) -> Optional[Dict]:
        """Return the raw YOLO detection best-matching a track by IoU."""
        best_det = None
        best_iou = 0.3   # minimum overlap threshold
        for det in raw_dets:
            iou = _bbox_iou(track_bbox, [float(v) for v in det["bbox"]])
            if iou > best_iou:
                best_iou = iou
                best_det = det
        return best_det

    # ── public API ────────────────────────────────────────────────────────────

    def run_inference(
        self,
        frame_bgr: np.ndarray,
        camera_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process one BGR frame through the full pipeline.

        Args:
            frame_bgr:  BGR image as numpy array (any resolution).
            camera_id:  String MongoDB camera ID — used for metadata only.

        Returns:
            Dict with keys: classification, confidence, detections, poses,
            tracks, suspicious_tracks, frame_metadata, processing_time_ms.
        """
        if not ai_service.is_ready():
            raise RuntimeError("AI Service not initialized")

        self._ensure_tracker()
        start = time.time()
        self._frame_idx += 1

        # ── 1. Detect persons (GPU — inference_lock) ──────────────────────
        with ai_service.inference_lock:
            raw_dets = ai_service.detector.detect(frame_bgr)

        # ── 2. Track locally (per-instance, no shared state) ──────────────
        tracks = self._tracker.update(raw_dets, frame_bgr)

        # ── 3. Crop person regions for ReID ───────────────────────────────
        crops:        List[np.ndarray] = []
        valid_tracks: List[Dict]       = []

        for t in tracks:
            crop = ai_service.reid.crop_person(frame_bgr, t["bbox"])
            if crop is not None:
                crops.append(crop)
                valid_tracks.append(t)

        # ── 4. Extract ReID embeddings (GPU — inference_lock) ─────────────
        embeddings: List[Optional[np.ndarray]] = []
        if crops:
            with ai_service.inference_lock:
                embeddings = ai_service.reid.extract_batch(crops)
        else:
            embeddings = []

        # ── 5. Match each track to a global ID ────────────────────────────
        # results: list of {track_id, global_id, bbox, x3d_score, det_conf}
        results: List[Dict] = []

        # Prevent Identity Hijacking: tracks within the SAME frame cannot share a global_id.
        # Pre-pass: claim all existing global IDs first so new tracks can't steal them.
        used_global_ids = set()
        with ai_service.state_lock:
            for track_info in valid_tracks:
                existing_gid = ai_service.db.get_global_id_for_track(
                    self._int_cam_id, track_info["track_id"]
                )
                if existing_gid is not None:
                    used_global_ids.add(existing_gid)

        for track_info, embedding in zip(valid_tracks, embeddings):
            if embedding is None:
                continue

            track_id = track_info["track_id"]
            bbox     = [float(v) for v in track_info["bbox"]]
            key      = (self._int_cam_id, track_id)

            # Smooth embedding over last 10 frames (per-instance, no lock)
            if key not in self._embed_buf:
                self._embed_buf[key] = collections.deque(maxlen=10)
            self._embed_buf[key].append(embedding)

            smoothed = np.mean(list(self._embed_buf[key]), axis=0)
            norm     = np.linalg.norm(smoothed)
            smoothed = smoothed / norm if norm > 1e-6 else embedding

            # Assign global ID (state_lock guards matcher + shared dicts)
            with ai_service.state_lock:
                existing_gid = ai_service.db.get_global_id_for_track(
                    self._int_cam_id, track_id
                )

                if existing_gid is not None:
                    # Known track — update embedding periodically
                    cnt = self._embed_update_cnt.get(key, 0)
                    if cnt % Config.EMBEDDING_UPDATE_INTERVAL == 0:
                        ai_service.db.update_identity(
                            existing_gid, smoothed,
                            self._int_cam_id, track_id,
                        )
                        ai_service.matcher.add_embedding(
                            smoothed, existing_gid, self._int_cam_id
                        )
                    self._embed_update_cnt[key] = cnt + 1
                    global_id = existing_gid

                else:
                    # New track — query FAISS + DB for a match
                    faiss_gid, faiss_score = ai_service.matcher.query(
                        smoothed, self._int_cam_id
                    )
                    db_gid, db_score = ai_service.db.find_match(
                        smoothed, self._int_cam_id
                    )

                    best_match_gid = None
                    if faiss_score >= db_score and faiss_gid is not None:
                        best_match_gid = faiss_gid
                    elif db_gid is not None:
                        best_match_gid = db_gid

                    # HIJACK PREVENTION: If the best match is already physically present
                    # in this frame, they cannot be the same person. Reject the match.
                    if best_match_gid is not None and best_match_gid in used_global_ids:
                        global_id = None
                    else:
                        global_id = best_match_gid

                    if global_id is not None:
                        ai_service.db.update_identity(
                            global_id, smoothed, self._int_cam_id, track_id
                        )
                        ai_service.matcher.add_embedding(
                            smoothed, global_id, self._int_cam_id
                        )
                    else:
                        # Register brand-new identity
                        global_id = ai_service.db.register_new_identity(
                            smoothed, self._int_cam_id, track_id
                        )
                        ai_service.matcher.add_embedding(
                            smoothed, global_id, self._int_cam_id
                        )

                    # Mark this ID as claimed so subsequent new tracks in this frame can't take it
                    used_global_ids.add(global_id)

                    # Ensure per-global-id score tracking slots exist
                    ai_service.theft_scores.setdefault(global_id, None)
                    ai_service.x3d_frame_counters.setdefault(global_id, 0)

            # Resolve detection confidence via IoU match
            matched_det = self._match_det_to_track(bbox, raw_dets)
            det_conf    = matched_det["confidence"] if matched_det else 0.0

            results.append({
                "track_id":  track_id,
                "global_id": global_id,
                "bbox":      bbox,
                "crop":      crops[valid_tracks.index(track_info)],
                "det_conf":  det_conf,
                "x3d_score": 0.0,   # filled in step 7
            })

        # ── 6. Feed crops into ClipBuffer (state_lock) ────────────────────
        with ai_service.state_lock:
            for res in results:
                ai_service.clip_buffer.add_frame(res["global_id"], res["crop"])

        # ── 7. X3D inference per global ID ────────────────────────────────
        # Run every Config.X3D_INFERENCE_EVERY frames per global_id.
        # get_clip() returns None until the buffer holds >= X3D_CLIP_FRAMES
        # frames, so no X3D call is wasted on short tracks.
        # Uniform temporal subsampling to SAMPLED_FRAMES=180 is done inside
        # ClipBuffer.get_clip() — we never touch that logic here.
        for res in results:
            gid = res["global_id"]

            with ai_service.state_lock:
                cnt = ai_service.x3d_frame_counters.get(gid, 0) + 1
                ai_service.x3d_frame_counters[gid] = cnt
                should_run = (cnt % Config.X3D_INFERENCE_EVERY == 0)
                clip = ai_service.clip_buffer.get_clip(gid) if should_run else None

            if clip is not None:
                # GPU call under inference_lock
                with ai_service.inference_lock:
                    score = ai_service.x3d.predict(clip)
                # Store result under state_lock
                with ai_service.state_lock:
                    ai_service.theft_scores[gid] = score
                res["x3d_score"] = score
                logger.debug(
                    "X3D G:%d  score=%.3f  (frame %d)", gid, score, self._frame_idx
                )
            else:
                # Use last known score for this global ID
                with ai_service.state_lock:
                    last = ai_service.theft_scores.get(gid)
                res["x3d_score"] = float(last) if last is not None else 0.0

        # ── 8. Build classification result ────────────────────────────────
        # Clarification #1 — only ≥ 0.80 triggers "theft"; ≥ 0.50 is
        # "normal" but flagged as suspicious in metadata.
        highest_score = max((r["x3d_score"] for r in results), default=0.0)

        if highest_score >= Config.X3D_THEFT_THRESHOLD:
            classification = "theft"
            confidence     = highest_score
        else:
            classification = "normal"
            confidence     = highest_score   # raw score, never clamped

        # suspicious_tracks: any global ID at or above suspicious threshold
        suspicious_tracks = [
            {
                "track_id":  res["track_id"],
                "global_id": res["global_id"],
                "x3d_score": res["x3d_score"],
            }
            for res in results
            if res["x3d_score"] >= Config.X3D_SUSPICIOUS_THRESHOLD
        ]

        # ── 9. Periodic maintenance ───────────────────────────────────────
        if self._frame_idx % self._PRUNE_EVERY == 0:
            ai_service.prune_expired_identities()
        if self._frame_idx % self._REBUILD_EVERY == 0:
            ai_service.rebuild_matcher_index()

        # ── 10. Assemble return dict (API contract preserved) ─────────────
        processing_time = (time.time() - start) * 1000.0

        # tracks list: include global_id as required by clarification #3
        tracks_out = [
            {
                "track_id":  res["track_id"],
                "global_id": res["global_id"],
                "bbox":      res["bbox"],
                "class":     "person",
                "confidence": res["det_conf"],
                "x3d_score": res["x3d_score"],
            }
            for res in results
        ]

        frame_metadata: Dict[str, Any] = {
            "frame_index":    self._frame_idx,
            "camera_id":      camera_id,
            "num_detections": len(raw_dets),
            "num_tracks":     len(tracks),
            "num_persons":    len(results),
            "raw_x3d_score":  highest_score,
        }
        # Add suspicious flag when score is in [0.50, 0.80)
        if highest_score >= Config.X3D_SUSPICIOUS_THRESHOLD:
            frame_metadata["suspicious"] = True

        return {
            "classification":     classification,
            "confidence":         confidence,
            "detections":         [
                {
                    "bbox":       [float(v) for v in d["bbox"]],
                    "confidence": d["confidence"],
                    "class":      "person",
                    "class_id":   d["class_id"],
                }
                for d in raw_dets
            ],
            "poses":              [],       # no pose model in new pipeline
            "tracks":             tracks_out,
            "suspicious_tracks":  suspicious_tracks,
            "frame_metadata":     frame_metadata,
            "processing_time_ms": processing_time,
        }

    # Backward-compatible alias — views.py calls runner.process_frame(...)
    process_frame = run_inference

    def reset(self) -> None:
        """Reset per-instance state (tracker + embedding buffers)."""
        self._tracker = None
        self._embed_buf.clear()
        self._embed_update_cnt.clear()
        self._frame_idx = 0
