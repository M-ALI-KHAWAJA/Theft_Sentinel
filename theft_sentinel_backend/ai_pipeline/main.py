"""
Multi-Camera Theft Detection System
====================================
Combines:
  • YOLOv8m       — person detection
  • DeepSORT      — per-camera local tracking
  • OSNet (ReID)  — cross-camera identity matching via FAISS
  • X3D-S         — per-person action classification (normal vs theft)

Pipeline per frame:
  1. Detect persons (YOLOv8m)
  2. Track locally (DeepSORT)
  3. Extract ReID embeddings (OSNet)
  4. Match across cameras → assign Global ID (FAISS + cosine)
  5. Accumulate person crops into per-global-ID clip buffers
  6. Periodically run X3D on each buffer → theft probability
  7. Display annotated tiled view

Press 'q' or ESC to quit.
Press 's' to print stats.
Press 'd' to toggle detection logging.
"""

import sys
import os
import time
import argparse
import collections
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_config.config import Config
from detection.detector import PersonDetector
from tracking.tracker import MultiObjectTracker
from reid.extractor import ReIDExtractor
from matching.matcher import CrossCameraMatcher
from database.identity_db import GlobalIdentityDatabase
from camera.stream import MultiCameraManager
from visualization.display import Visualizer
from x3d.classifier import ClipBuffer, TheftClassifier


# ─────────────────────────────────────────────────────────────────────────────


class MCMTTheftPipeline:
    """
    Main orchestrator for multi-camera theft detection.

    Extends the MCMT-ReID pipeline with X3D-based action classification.
    Each global identity gets its own clip buffer; X3D scores are
    maintained per global ID and shown in the visualization.
    """

    def __init__(self, sources: list = None, camera_ids: list = None):
        self.sources    = sources    or Config.CAMERA_SOURCES
        self.camera_ids = camera_ids or Config.CAMERA_IDS[:len(self.sources)]

        print("=" * 65)
        print("  Multi-Camera Theft Detection System")
        print("=" * 65)
        print(f"  Device     : {Config.DEVICE}")
        print(f"  Cameras    : {len(self.sources)}")
        print(f"  YOLO model : {Config.YOLO_MODEL}")
        print(f"  X3D model  : {Config.X3D_MODEL_PATH}")
        print(f"  Theft thr  : {Config.X3D_THEFT_THRESHOLD:.0%}")
        print("=" * 65)

        # ── Standard MCMT modules ─────────────────────────────────────────
        print("\n[Init] Loading modules...")
        self.detector        = PersonDetector()
        self.reid            = ReIDExtractor()
        self.matcher         = CrossCameraMatcher()
        self.db              = GlobalIdentityDatabase()
        self.camera_manager  = MultiCameraManager()
        self.visualizer      = Visualizer()

        self.trackers: dict[int, MultiObjectTracker] = {
            cam_id: MultiObjectTracker(cam_id) for cam_id in self.camera_ids
        }

        # ── X3D modules ───────────────────────────────────────────────────
        print("[Init] Loading X3D classifier...")
        self.clip_buffer  = ClipBuffer(max_frames=Config.X3D_CLIP_FRAMES)
        self.x3d          = TheftClassifier(Config.X3D_MODEL_PATH, Config.DEVICE)

        # global_id → latest theft probability (None = not yet scored)
        self.theft_scores: dict[int, float | None] = {}

        # global_id → frame counter (to control inference rate)
        self._x3d_frame_counters: dict[int, int] = {}

        # global_id → whether alert was already printed
        self._alerted: set[int] = set()

        # ── MCMT bookkeeping ──────────────────────────────────────────────
        self._frame_counter = 0
        self._prune_interval   = 300
        self._rebuild_interval = 500
        self._start_time = time.time()
        self._fps        = 0.0
        self._running    = False

        self._embedding_update_counters: dict[tuple, int] = {}
        self._track_embeddings_buffer: dict[tuple, collections.deque] = {}

        print("[Init] All modules loaded.\n")

    # ── camera startup ────────────────────────────────────────────────────────

    def start_cameras(self) -> bool:
        print("[Pipeline] Starting camera streams...")
        ok = 0
        for src, cam_id in zip(self.sources, self.camera_ids):
            if self.camera_manager.add_camera(src, cam_id):
                ok += 1
            else:
                print(f"[Pipeline] WARNING: Cannot open camera {cam_id}: {src}")
        if ok == 0:
            print("[Pipeline] ERROR: No cameras started.")
            return False
        time.sleep(1.0)
        print(f"[Pipeline] {ok}/{len(self.sources)} cameras active\n")
        return True

    # ── per-camera processing ─────────────────────────────────────────────────

    def process_camera(
        self,
        camera_id: int,
        frame: np.ndarray,
    ) -> tuple[np.ndarray, list[dict]]:
        """
        Full detection → tracking → ReID → matching pipeline for one camera.

        Also feeds person crops into the X3D clip buffer using global IDs.

        Returns:
            (annotated_frame, list of result dicts)
        """
        # ── 1. Detect ──────────────────────────────────────────────────────
        raw_detections = self.detector.detect(frame)

        # ── 2. Track ───────────────────────────────────────────────────────
        tracks = self.trackers[camera_id].update(raw_detections, frame)

        # ── 3. Crop + ReID ─────────────────────────────────────────────────
        crops       = []
        track_infos = []
        for track in tracks:
            crop = self.reid.crop_person(frame, track["bbox"])
            if crop is not None:
                crops.append(crop)
                track_infos.append(track)

        embeddings = self.reid.extract_batch(crops) if crops else []

        # ── 4. Match / assign global IDs ───────────────────────────────────
        results = []
        for track_info, embedding in zip(track_infos, embeddings):
            if embedding is None:
                continue

            track_id = track_info["track_id"]
            bbox     = track_info["bbox"]
            key      = (camera_id, track_id)

            # Smooth embedding over last 10 frames
            if key not in self._track_embeddings_buffer:
                self._track_embeddings_buffer[key] = collections.deque(maxlen=10)
            self._track_embeddings_buffer[key].append(embedding)

            smoothed = np.mean(list(self._track_embeddings_buffer[key]), axis=0)
            norm = np.linalg.norm(smoothed)
            smoothed = smoothed / norm if norm > 0 else embedding

            existing_gid = self.db.get_global_id_for_track(camera_id, track_id)

            if existing_gid is not None:
                counter = self._embedding_update_counters.get(key, 0)
                if counter % Config.EMBEDDING_UPDATE_INTERVAL == 0:
                    self.db.update_identity(existing_gid, smoothed, camera_id, track_id)
                    self.matcher.add_embedding(smoothed, existing_gid, camera_id)
                self._embedding_update_counters[key] = counter + 1
                global_id   = existing_gid
                match_score = 1.0
            else:
                global_id, match_score = self._match_globally(smoothed, camera_id)
                if global_id is not None:
                    self.db.update_identity(global_id, smoothed, camera_id, track_id)
                    self.matcher.add_embedding(smoothed, global_id, camera_id)
                else:
                    global_id = self.db.register_new_identity(smoothed, camera_id, track_id)
                    self.matcher.add_embedding(smoothed, global_id, camera_id)
                    match_score = 0.0
                    # Initialise theft score entry
                    self.theft_scores.setdefault(global_id, None)

            results.append({
                "camera_id":   camera_id,
                "track_id":    track_id,
                "global_id":   global_id,
                "bbox":        bbox,
                "match_score": match_score,
                "crop":        crops[track_infos.index(track_info)],  # raw crop for X3D
            })

        # ── 5. Feed crops into X3D clip buffer ─────────────────────────────
        for res in results:
            gid  = res["global_id"]
            crop = res["crop"]
            self.clip_buffer.add_frame(gid, crop)

        # ── 6. Draw (theft scores injected) ────────────────────────────────
        annotated = self.visualizer.draw_detections(
            frame, results, camera_id, theft_scores=self.theft_scores
        )

        return annotated, results

    # ── X3D inference ─────────────────────────────────────────────────────────

    def run_x3d_inference(self):
        """
        Periodically run X3D on every global identity that has enough frames.
        Each identity has its own frame counter so inference is staggered.
        """
        for gid in list(self.theft_scores.keys()):
            # Increment per-identity counter
            cnt = self._x3d_frame_counters.get(gid, 0) + 1
            self._x3d_frame_counters[gid] = cnt

            if cnt % Config.X3D_INFERENCE_EVERY != 0:
                continue

            buf_size = self.clip_buffer.buffer_size(gid)
            clip = self.clip_buffer.get_clip(gid)

            if clip is None:
                print(f"[X3D] G:{gid} buffer {buf_size}/{Config.X3D_CLIP_FRAMES} frames")
                continue

            score = self.x3d.predict(clip)
            self.theft_scores[gid] = score

            if score >= Config.X3D_THEFT_THRESHOLD:
                print(f"[X3D] 🚨 THEFT  G:{gid} score={score:.2%}")
                if gid not in self._alerted:
                    self._alerted.add(gid)
            elif score >= Config.X3D_SUSPICIOUS_THRESHOLD:
                print(f"[X3D] ⚠  Suspicious G:{gid} score={score:.2%}")
            else:
                print(f"[X3D] ✅ Normal     G:{gid} score={score:.2%}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _match_globally(
        self,
        embedding: np.ndarray,
        camera_id: int,
    ) -> tuple[int | None, float]:
        faiss_gid, faiss_score = self.matcher.query(embedding, camera_id)
        db_gid,    db_score    = self.db.find_match(embedding, camera_id)

        if faiss_score >= db_score and faiss_gid is not None:
            return faiss_gid, faiss_score
        if db_gid is not None:
            return db_gid, db_score
        return None, 0.0

    def _periodic_maintenance(self):
        self._frame_counter += 1

        if self._frame_counter % self._prune_interval == 0:
            pruned_ids = self._get_expired_global_ids()
            self.db.prune_expired()
            # Clean up X3D state for pruned identities
            for gid in pruned_ids:
                self.theft_scores.pop(gid, None)
                self._x3d_frame_counters.pop(gid, None)
                self._alerted.discard(gid)
                self.clip_buffer.remove_person(gid)

        if self._frame_counter % self._rebuild_interval == 0:
            identities = self.db.get_all_identities()
            identity_data = {
                gid: {"embedding_buffer": list(rec.embedding_buffer)}
                for gid, rec in identities.items()
            }
            self.matcher.rebuild_index(identity_data)

    def _get_expired_global_ids(self) -> list[int]:
        """Return global IDs that are about to be pruned."""
        import time as _time
        return [
            gid for gid, rec in self.db.get_all_identities().items()
            if rec.is_expired()
        ]

    def _print_stats(self):
        stats   = self.db.get_stats()
        runtime = time.time() - self._start_time
        alerts  = len(self._alerted)

        print("\n" + "=" * 55)
        print("  System Statistics")
        print("=" * 55)
        print(f"  Runtime          : {runtime:.1f}s")
        print(f"  Pipeline FPS     : {self._fps:.1f}")
        print(f"  Global IDs       : {stats['total_identities']}")
        print(f"  Active Tracks    : {stats['active_tracks']}")
        print(f"  FAISS Index Size : {self.matcher.get_index_size()}")
        print(f"  Frames Processed : {self._frame_counter}")
        print(f"  Theft Alerts     : {alerts}")
        print("=" * 55)

        for gid, score in self.theft_scores.items():
            score_str = f"{score:.2%}" if score is not None else "pending"
            alert_str = " 🚨 ALERT" if gid in self._alerted else ""
            print(f"  G:{gid:3d}  theft_score={score_str}{alert_str}")
        print()

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        if not self.start_cameras():
            return

        self._running = True
        print("[Pipeline] Starting main loop... Press 'q' to quit.\n")

        fps_counter = 0
        fps_start   = time.time()

        try:
            while self._running:
                frames = self.camera_manager.get_all_frames()
                if not frames:
                    time.sleep(0.01)
                    continue

                annotated_frames = {}
                all_detections   = []

                for cam_id, frame in frames.items():
                    # Resize from 4K to 720p before processing
                    frame = cv2.resize(frame, (Config.FRAME_WIDTH, Config.FRAME_HEIGHT))

                    annotated, detections = self.process_camera(cam_id, frame)
                    annotated_frames[cam_id] = annotated
                    all_detections.extend(detections)

                # ── X3D inference (after all cameras processed) ────────────
                self.run_x3d_inference()

                # ── Periodic maintenance ───────────────────────────────────
                self._periodic_maintenance()

                # ── FPS ───────────────────────────────────────────────────
                fps_counter += 1
                elapsed = time.time() - fps_start
                if elapsed >= 1.0:
                    self._fps   = fps_counter / elapsed
                    fps_counter = 0
                    fps_start   = time.time()

                # ── Display ───────────────────────────────────────────────
                display = self.visualizer.create_tiled_display(annotated_frames)

                db_stats = self.db.get_stats()
                db_stats.update({
                    "fps":          self._fps,
                    "faiss_size":   self.matcher.get_index_size(),
                    "theft_alerts": len(self._alerted),
                })
                display = self.visualizer.draw_stats_overlay(display, db_stats)

                cv2.imshow("Multi-Camera Theft Detection", display)

                if Config.LOG_DETECTIONS:
                    for det in all_detections:
                        score = self.theft_scores.get(det["global_id"])
                        score_str = f"{score:.2%}" if score is not None else "---"
                        print(f"  Cam:{det['camera_id']} "
                              f"Track:{det['track_id']} "
                              f"Global:{det['global_id']} "
                              f"Theft:{score_str} "
                              f"ReID:{det['match_score']:.2f}")

                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), 27):
                    print("\n[Pipeline] Quit signal received")
                    break
                elif key == ord('s'):
                    self._print_stats()
                elif key == ord('d'):
                    Config.LOG_DETECTIONS = not Config.LOG_DETECTIONS
                    print(f"[Pipeline] Detection logging: "
                          f"{'ON' if Config.LOG_DETECTIONS else 'OFF'}")

        except KeyboardInterrupt:
            print("\n[Pipeline] Interrupted by user")
        finally:
            self.shutdown()

    def shutdown(self):
        self._running = False
        self.camera_manager.stop_all()
        cv2.destroyAllWindows()

        # Print final summary
        print("\n" + "=" * 55)
        print("  Session Summary")
        print("=" * 55)
        print(f"  Frames processed : {self._frame_counter}")
        print(f"  Average FPS      : {self._fps:.1f}")
        print(f"  Total alerts     : {len(self._alerted)}")
        if self._alerted:
            print(f"  Alerted IDs      : {sorted(self._alerted)}")
        print("=" * 55)
        print("[Pipeline] Shutdown complete")


# ─── CLI ─────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Camera Theft Detection (YOLOv8m + DeepSORT + OSNet + X3D)"
    )
    parser.add_argument("--sources", nargs="+", default=None,
                        help="Video sources (file paths, RTSP URLs, device indices)")
    parser.add_argument("--camera-ids", nargs="+", type=int, default=None)
    parser.add_argument("--x3d-model", type=str, default=None,
                        help="Path to trained X3D .pth file")
    parser.add_argument("--theft-threshold", type=float, default=None,
                        help="X3D theft probability threshold (default 0.80)")
    parser.add_argument("--yolo-model", type=str, default=None)
    parser.add_argument("--yolo-conf", type=float, default=None)
    parser.add_argument("--max-age", type=int, default=None)
    parser.add_argument("--log-detections", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.x3d_model:
        Config.X3D_MODEL_PATH = args.x3d_model
    if args.theft_threshold:
        Config.X3D_THEFT_THRESHOLD = args.theft_threshold
    if args.yolo_model:
        Config.YOLO_MODEL = args.yolo_model
    if args.yolo_conf:
        Config.YOLO_CONFIDENCE = args.yolo_conf
    if args.max_age:
        Config.DEEPSORT_MAX_AGE = args.max_age
    if args.log_detections:
        Config.LOG_DETECTIONS = True

    sources = args.sources
    if sources:
        sources = [int(s) if s.isdigit() else s for s in sources]

    pipeline = MCMTTheftPipeline(sources=sources, camera_ids=args.camera_ids)
    pipeline.run()


if __name__ == "__main__":
    main()
