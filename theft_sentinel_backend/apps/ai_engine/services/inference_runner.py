"""
Inference Runner
Wraps your existing AI pipeline without modifying it
Processes frames through: YOLO Detection -> DeepSORT -> Pose -> ML Classifier
"""
import sys
import cv2
import time
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)

# Add ModelExport to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_EXPORT_PATH = BASE_DIR / "ModelExport"
sys.path.insert(0, str(MODEL_EXPORT_PATH))

from ml_classifier.feature_builder import MLFeatureBuilder
from ml_classifier.sequence_collector import SequenceCollector
from .ai_service import ai_service


class Detection:
    """Wrapper for YOLO detection output (from your pipeline)"""
    def __init__(self, bbox: List[float], conf: float, coco_class: int):
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.conf = conf
        self.coco_class = coco_class
        self.logical_class = self._map_class()
        self.area = self._calculate_area()

    def _calculate_area(self) -> float:
        return max(0.0, self.bbox[2] - self.bbox[0]) * max(0.0, self.bbox[3] - self.bbox[1])

    def _map_class(self) -> str:
        """Map COCO classes to logical types"""
        if self.coco_class == 0:  # person
            return "person"
        elif self.coco_class in {24, 26, 28}:  # backpack, handbag, suitcase
            return "bag"
        elif self.coco_class in {67, 73}:  # cell phone, book
            return "suspicious_object"
        else:
            return "object"

    def is_valid(self, min_conf=0.45, min_area=450) -> bool:
        return self.conf >= min_conf and self.area >= min_area


class PoseDetection:
    """Pose estimation result for a single person"""
    def __init__(self, bbox: List[float], keypoints: np.ndarray, conf: float):
        self.bbox = bbox  # [x1,y1,x2,y2]
        self.keypoints = keypoints  # (17,3)
        self.conf = conf


class TrackInfo:
    """Per-track information (from your pipeline)"""
    def __init__(self, track_id: int, coco_class: int, logical_class: str):
        self.track_id = track_id
        self.coco_class = coco_class
        self.label = logical_class
        
        self.first_seen = 0
        self.last_seen = 0
        
        self.bbox_history = deque(maxlen=10)
        self.conf_history = deque(maxlen=10)
        
        self.pose_history = deque(maxlen=30)
        self.feature_history = deque(maxlen=30)
        
        # Behavioral counters (for theft detection)
        self.hand_in_bag_frames = 0
        self.hand_in_torso_frames = 0
        self.fast_wrist_frames = 0
        self.near_object_frames = 0
        self.recent_concealment_events = 0
        self.prev_wrist_region = "none"
        
        # ML score
        self.ml_score = 0.0

    def update_bbox(self, frame_num: int, bbox: List[float], conf: float):
        self.last_seen = frame_num
        if not self.bbox_history:
            self.first_seen = frame_num
        self.bbox_history.append(bbox)
        self.conf_history.append(conf)

    def update_pose(self, pose_det: PoseDetection, features: dict):
        self.pose_history.append(pose_det)
        self.feature_history.append(features)

    def get_smoothed_bbox(self) -> Optional[List[float]]:
        if not self.bbox_history:
            return None
        if len(self.bbox_history) >= 2:
            cur = self.bbox_history[-1]
            prev = self.bbox_history[-2]
            return [
                0.7 * cur[0] + 0.3 * prev[0],
                0.7 * cur[1] + 0.3 * prev[1],
                0.7 * cur[2] + 0.3 * prev[2],
                0.7 * cur[3] + 0.3 * prev[3],
            ]
        return list(self.bbox_history[-1])

    def get_avg_conf(self) -> float:
        if not self.conf_history:
            return 0.0
        return float(np.mean(self.conf_history))

    def get_dwell_time(self) -> int:
        return self.last_seen - self.first_seen if self.last_seen and self.first_seen else 0

    def has_pose(self) -> bool:
        return len(self.pose_history) > 0

    def latest_pose(self) -> Optional[PoseDetection]:
        return self.pose_history[-1] if self.pose_history else None

    def latest_features(self) -> Optional[dict]:
        return self.feature_history[-1] if self.feature_history else None


class PoseFeatureEngine:
    """Compute pose-based features (from your pipeline)"""
    
    @staticmethod
    def compute_features(pose: PoseDetection, prev_pose: Optional[PoseDetection]) -> dict:
        kps = pose.keypoints
        xy = kps[:, :2]
        
        # Keypoint indices
        NOSE = 0
        L_SH, R_SH = 5, 6
        L_EL, R_EL = 7, 8
        L_WR, R_WR = 9, 10
        L_HIP, R_HIP = 11, 12
        
        nose = xy[NOSE]
        l_sh, r_sh = xy[L_SH], xy[R_SH]
        l_el, r_el = xy[L_EL], xy[R_EL]
        l_wr, r_wr = xy[L_WR], xy[R_WR]
        l_hip, r_hip = xy[L_HIP], xy[R_HIP]
        
        mid_sh = (l_sh + r_sh) / 2.0
        mid_hip = (l_hip + r_hip) / 2.0
        
        # Angles
        torso_vec = mid_sh - mid_hip
        torso_angle = float(np.degrees(np.arctan2(torso_vec[0], torso_vec[1])))
        
        head_vec = nose - mid_sh
        head_angle = float(np.degrees(np.arctan2(head_vec[0], head_vec[1])))
        
        # Elbow angles
        left_elbow_angle = PoseFeatureEngine._keypoint_angle(l_sh, l_el, l_wr)
        right_elbow_angle = PoseFeatureEngine._keypoint_angle(r_sh, r_el, r_wr)
        
        # Wrist to hip distances
        left_wrist_to_hip = PoseFeatureEngine._distance(l_wr, mid_hip)
        right_wrist_to_hip = PoseFeatureEngine._distance(r_wr, mid_hip)
        
        # Wrist speeds
        left_wrist_speed = 0.0
        right_wrist_speed = 0.0
        if prev_pose is not None:
            prev_xy = prev_pose.keypoints[:, :2]
            prev_l_wr = prev_xy[L_WR]
            prev_r_wr = prev_xy[R_WR]
            left_wrist_speed = PoseFeatureEngine._distance(l_wr, prev_l_wr)
            right_wrist_speed = PoseFeatureEngine._distance(r_wr, prev_r_wr)
        
        return {
            "torso_angle": torso_angle,
            "head_angle": head_angle,
            "left_elbow_angle": left_elbow_angle,
            "right_elbow_angle": right_elbow_angle,
            "left_wrist_to_hip": left_wrist_to_hip,
            "right_wrist_to_hip": right_wrist_to_hip,
            "left_wrist_speed": left_wrist_speed,
            "right_wrist_speed": right_wrist_speed,
        }
    
    @staticmethod
    def _keypoint_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        v1 = a - b
        v2 = c - b
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        cos_ang = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_ang)))
    
    @staticmethod
    def _distance(p1: np.ndarray, p2: np.ndarray) -> float:
        return float(np.linalg.norm(p1 - p2))


def bbox_iou(b1: List[float], b2: List[float]) -> float:
    """Calculate IoU between two bboxes"""
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


class InferenceRunner:
    """
    Runs inference on a single frame
    Uses YOUR EXISTING PIPELINE logic without modification
    """
    
    def __init__(self):
        self.sequence_collector = SequenceCollector(window=10)
        self.tracks: Dict[int, TrackInfo] = {}
        self.frame_idx = 0
        
        # Config (matching your pipeline)
        self.det_conf = 0.45
        self.det_iou = 0.50
        self.det_imgsz = 704
        self.pose_conf = 0.30
        self.pose_iou = 0.50
        self.pose_imgsz = 320
        self.pose_crop_pad = 0.25
    
    def process_frame(self, frame: np.ndarray, camera_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single frame through the full pipeline
        Returns detection results and theft classification
        """
        start_time = time.time()
        
        if not ai_service.is_ready():
            raise RuntimeError("AI Service not initialized")
        
        self.frame_idx += 1
        
        # Step 1: Detection
        detections = self._run_detection(frame)
        
        # Step 2: Tracking
        tracks_data = self._run_tracking(frame, detections)
        
        # Step 3: Pose estimation (only for persons)
        poses = self._run_pose_estimation(frame)
        
        # Step 4: ML Classification
        classification_result = self._run_classification()
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Build response
        result = {
            "detections": detections,
            "poses": poses,
            "tracks": tracks_data,
            "classification": classification_result["classification"],
            "confidence": classification_result["confidence"],
            "suspicious_tracks": classification_result["suspicious_tracks"],
            "frame_metadata": {
                "frame_index": self.frame_idx,
                "camera_id": camera_id,
                "num_detections": len(detections),
                "num_tracks": len(tracks_data),
                "num_persons": sum(1 for d in detections if d["class"] == "person"),
            },
            "processing_time_ms": processing_time
        }
        
        return result
    
    def _run_detection(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run YOLO detection"""
        det_results = ai_service.det_model(
            frame,
            imgsz=self.det_imgsz,
            conf=self.det_conf,
            iou=self.det_iou,
            verbose=False
        )
        
        detections = []
        det_res = det_results[0]
        
        if det_res.boxes is not None:
            for box in det_res.boxes:
                cls_id = int(box.cls.cpu().item())
                conf = float(box.conf.cpu().item())
                xyxy = box.xyxy.cpu().numpy()[0]
                bbox = [float(v) for v in xyxy]
                
                det_obj = Detection(bbox, conf, cls_id)
                if det_obj.is_valid():
                    detections.append({
                        "bbox": bbox,
                        "confidence": conf,
                        "class": det_obj.logical_class,
                        "class_id": cls_id,
                    })
        
        return detections
    
    def _run_tracking(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run DeepSORT tracking"""
        # Prepare DeepSORT input
        deepsort_input = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            tlwh = [x1, y1, x2 - x1, y2 - y1]
            deepsort_input.append((tlwh, det["confidence"], det["class"]))
        
        # Update tracker
        ds_tracks = ai_service.deepsort.update_tracks(deepsort_input, frame=frame)
        
        # Update our internal tracks
        active_ids = set()
        tracks_output = []
        
        for t in ds_tracks:
            if not t.is_confirmed():
                continue
            
            tid = t.track_id
            active_ids.add(tid)
            bbox = [float(v) for v in t.to_ltrb()]
            
            # Find matching detection
            best_det = None
            best_iou = 0.0
            for det in detections:
                iou = bbox_iou(bbox, det["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_det = det
            
            if best_det is None or best_iou < 0.3:
                continue
            
            coco_class = best_det["class_id"]
            logical_class = best_det["class"]
            conf = best_det["confidence"]
            
            # Create or update track
            if tid not in self.tracks:
                self.tracks[tid] = TrackInfo(tid, coco_class, logical_class)
            else:
                self.tracks[tid].coco_class = coco_class
                self.tracks[tid].label = logical_class
            
            self.tracks[tid].update_bbox(self.frame_idx, bbox, conf)
            
            tracks_output.append({
                "track_id": tid,
                "bbox": bbox,
                "class": logical_class,
                "confidence": conf,
                "dwell_time": self.tracks[tid].get_dwell_time(),
                "ml_score": self.tracks[tid].ml_score,
            })
        
        # Remove dead tracks
        for tid in list(self.tracks.keys()):
            if tid not in active_ids:
                del self.tracks[tid]
        
        return tracks_output
    
    def _run_pose_estimation(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Run pose estimation on person tracks"""
        poses_output = []
        
        # Get person tracks
        person_tracks = [
            (tid, t) for tid, t in self.tracks.items()
            if t.label == "person" and t.get_smoothed_bbox() is not None
        ]
        
        if not person_tracks:
            return poses_output
        
        H, W = frame.shape[:2]
        crops = []
        crop_meta = []
        
        # Create crops for each person
        for tid, track in person_tracks:
            bbox = track.get_smoothed_bbox()
            x1, y1, x2, y2 = bbox
            w = x2 - x1
            h = y2 - y1
            pad_x = w * self.pose_crop_pad
            pad_y = h * self.pose_crop_pad
            cx1 = max(0, int(x1 - pad_x))
            cy1 = max(0, int(y1 - pad_y))
            cx2 = min(W - 1, int(x2 + pad_x))
            cy2 = min(H - 1, int(y2 + pad_y))
            
            if cx2 <= cx1 or cy2 <= cy1:
                continue
            
            crop = frame[cy1:cy2, cx1:cx2]
            if crop.size == 0:
                continue
            
            crops.append(crop)
            crop_meta.append((tid, cx1, cy1, track))
        
        if not crops:
            return poses_output
        
        # Batch pose inference
        pose_results = ai_service.pose_model(
            crops,
            imgsz=self.pose_imgsz,
            conf=self.pose_conf,
            iou=self.pose_iou,
            verbose=False
        )
        
        # Process pose results and update tracks
        for idx, res in enumerate(pose_results):
            tid, base_x, base_y, track = crop_meta[idx]
            
            if res.boxes is None or res.keypoints is None or len(res.boxes) == 0:
                continue
            
            boxes = res.boxes.xyxy.cpu().numpy()
            scores = res.boxes.conf.cpu().numpy()
            classes = res.boxes.cls.cpu().numpy().astype(int)
            kpts = res.keypoints.data.cpu().numpy()
            
            # Find best person detection
            best_idx = -1
            best_score = 0.0
            for i in range(len(boxes)):
                if classes[i] != 0:  # person class
                    continue
                if scores[i] > best_score:
                    best_score = scores[i]
                    best_idx = i
            
            if best_idx < 0:
                continue
            
            # Convert to full frame coordinates
            kps_crop = kpts[best_idx]
            kps_full = kps_crop.copy()
            kps_full[:, 0] += base_x
            kps_full[:, 1] += base_y
            
            bbox_full = [
                float(boxes[best_idx][0] + base_x),
                float(boxes[best_idx][1] + base_y),
                float(boxes[best_idx][2] + base_x),
                float(boxes[best_idx][3] + base_y),
            ]
            
            pose_det = PoseDetection(bbox=bbox_full, keypoints=kps_full, conf=float(best_score))
            prev_pose = track.latest_pose()
            features = PoseFeatureEngine.compute_features(pose_det, prev_pose)
            track.update_pose(pose_det, features)
            
            # Behavioral analysis (from your pipeline)
            self._analyze_behavior(tid, track, kps_full)
            
            poses_output.append({
                "track_id": tid,
                "keypoints": kps_full.tolist(),
                "confidence": float(best_score),
                "features": features
            })
        
        return poses_output
    
    def _analyze_behavior(self, tid: int, track: TrackInfo, kps_full: np.ndarray):
        """Analyze suspicious behavior (from your pipeline logic)"""
        rw = kps_full[10][:2]  # right wrist
        lw = kps_full[9][:2]   # left wrist
        mid_hip = (kps_full[11][:2] + kps_full[12][:2]) / 2.0
        mid_shoulder = (kps_full[5][:2] + kps_full[6][:2]) / 2.0
        torso_top = mid_shoulder[1]
        torso_bottom = mid_hip[1]
        
        # Check hand in bag
        for other_tid, other_track in self.tracks.items():
            if other_tid == tid:
                continue
            if other_track.label == "bag":
                bag_bbox = other_track.get_smoothed_bbox()
                if bag_bbox is not None:
                    bx1, by1, bx2, by2 = bag_bbox
                    if bx1 <= rw[0] <= bx2 and by1 <= rw[1] <= by2:
                        track.hand_in_bag_frames += 1
                    if bx1 <= lw[0] <= bx2 and by1 <= lw[1] <= by2:
                        track.hand_in_bag_frames += 1
        
        # Check hand in torso region
        if torso_top <= rw[1] <= torso_bottom:
            track.hand_in_torso_frames += 1
        if torso_top <= lw[1] <= torso_bottom:
            track.hand_in_torso_frames += 1
        
        # Check fast wrist motion
        features = track.latest_features()
        if features:
            if features["right_wrist_speed"] > 15 or features["left_wrist_speed"] > 15:
                track.fast_wrist_frames += 1
        
        # Check near object interaction
        for other_tid, other_track in self.tracks.items():
            if other_tid == tid:
                continue
            if other_track.label == "object":
                ob = other_track.get_smoothed_bbox()
                if ob is not None:
                    ox1, oy1, ox2, oy2 = ob
                    if ox1 - 40 <= rw[0] <= ox2 + 40 and oy1 - 40 <= rw[1] <= oy2 + 40:
                        track.near_object_frames += 1
                    if ox1 - 40 <= lw[0] <= ox2 + 40 and oy1 - 40 <= lw[1] <= oy2 + 40:
                        track.near_object_frames += 1
        
        # Detect concealment events
        region_now = "none"
        if track.near_object_frames > 0:
            region_now = "object"
        if track.hand_in_bag_frames > 0:
            region_now = "bag"
        if track.hand_in_torso_frames > 0:
            region_now = "torso"
        
        if track.prev_wrist_region == "object" and region_now in ("torso", "bag"):
            track.recent_concealment_events += 1
        
        track.prev_wrist_region = region_now
    
    def _run_classification(self) -> Dict[str, Any]:
        """Run ML classification on tracked persons"""
        theft_detected = False
        max_confidence = 0.0
        suspicious_tracks = []
        
        for tid, track in self.tracks.items():
            if track.label != "person":
                continue
            
            # Build feature vector
            vec = MLFeatureBuilder.build_feature_vector(track)
            if vec is None:
                continue
            
            # Add to sequence collector
            self.sequence_collector.add(tid, vec)
            
            # Get sequence for classification
            seq = self.sequence_collector.get_sequence(tid, min_frames=3)
            
            if seq is not None and ai_service.ml_classifier.model is not None:
                try:
                    ml_score = ai_service.ml_classifier.predict(seq)
                    track.ml_score = float(ml_score)
                    
                    if ml_score > max_confidence:
                        max_confidence = ml_score
                    
                    if ml_score > 0.5:  # Theft threshold
                        theft_detected = True
                        suspicious_tracks.append({
                            "track_id": tid,
                            "ml_score": float(ml_score),
                            "behavior": {
                                "hand_in_bag": track.hand_in_bag_frames,
                                "hand_in_torso": track.hand_in_torso_frames,
                                "fast_wrist": track.fast_wrist_frames,
                                "near_object": track.near_object_frames,
                                "concealment_events": track.recent_concealment_events,
                            }
                        })
                except Exception as e:
                    logger.error(f"ML classification error: {str(e)}")
        
        return {
            "classification": "theft" if theft_detected else "normal",
            "confidence": float(max_confidence),
            "suspicious_tracks": suspicious_tracks
        }
    
    def reset(self):
        """Reset tracking state"""
        self.tracks.clear()
        self.frame_idx = 0
        self.sequence_collector = SequenceCollector(window=10)

