"""
Person Detection Module — YOLOv8 (Ultralytics).

Detects persons in a frame and returns bounding boxes + confidence scores.
Only the 'person' class (COCO class 0) is kept.
"""

import numpy as np
from ultralytics import YOLO
from ai_pipeline.ai_config.config import Config


class PersonDetector:
    """YOLOv8-based person detector optimized for real-time inference."""

    def __init__(self):
        """
        Initialize the YOLOv8 model.
        Downloads the model weights automatically on first run.
        """
        self.model = YOLO(Config.YOLO_MODEL)
        # Move to device (GPU if available)
        self.model.to(Config.DEVICE)
        self.conf_threshold = Config.YOLO_CONFIDENCE
        self.iou_threshold = Config.YOLO_IOU_THRESHOLD
        self.person_class_id = Config.YOLO_PERSON_CLASS_ID
        self.img_size = Config.YOLO_IMG_SIZE

        print(f"[Detector] YOLOv8 loaded: {Config.YOLO_MODEL} on {Config.DEVICE}")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Run person detection on a single frame.

        Args:
            frame: BGR image as numpy array (H, W, 3).

        Returns:
            List of detections, each a dict with keys:
                - 'bbox': [x1, y1, x2, y2] (pixel coords, int)
                - 'confidence': float
                - 'class_id': int (always 0 for person)
        """
        # Run inference — verbose=False suppresses per-frame logs
        results = self.model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.img_size,
            classes=[self.person_class_id],  # Only detect persons
            verbose=False,
        )

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            for box in boxes:
                # Extract bounding box (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())

                detections.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": conf,
                    "class_id": cls_id,
                })

        return detections

    def detect_batch(self, frames: list[np.ndarray]) -> list[list[dict]]:
        """
        Run person detection on a batch of frames.

        Args:
            frames: List of BGR images.

        Returns:
            List of detection lists, one per frame.
        """
        results = self.model(
            frames,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.img_size,
            classes=[self.person_class_id],
            verbose=False,
        )

        all_detections = []
        for result in results:
            frame_detections = []
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())

                    frame_detections.append({
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "confidence": conf,
                        "class_id": cls_id,
                    })
            all_detections.append(frame_detections)

        return all_detections
