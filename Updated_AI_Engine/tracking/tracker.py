"""
Multi-Object Tracking Module — DeepSORT.

Wraps the deep_sort_realtime library to maintain per-camera local track IDs.
Each camera gets its own tracker instance for independent tracking.
"""

import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from config.config import Config


class MultiObjectTracker:
    """
    DeepSORT-based multi-object tracker for a single camera.

    Maintains stable local track IDs, handles short occlusions,
    and returns tracked bounding boxes + IDs per frame.
    """

    def __init__(self, camera_id: int):
        """
        Initialize the DeepSORT tracker for one camera.

        Args:
            camera_id: Unique identifier for this camera.
        """
        self.camera_id = camera_id

        # Initialize DeepSORT with tuned parameters
        self.tracker = DeepSort(
            max_age=Config.DEEPSORT_MAX_AGE,
            n_init=Config.DEEPSORT_N_INIT,
            max_iou_distance=Config.DEEPSORT_MAX_IOU_DISTANCE,
            max_cosine_distance=Config.DEEPSORT_MAX_COSINE_DISTANCE,
            nn_budget=Config.DEEPSORT_NN_BUDGET,
            embedder="mobilenet",  # Re-enable DeepSORT's local embedder for stable tracking
        )

        print(f"[Tracker] DeepSORT initialized for Camera {camera_id}")

    def update(self, detections: list[dict], frame: np.ndarray) -> list[dict]:
        """
        Update the tracker with new detections for the current frame.

        Args:
            detections: List of dicts with 'bbox' [x1,y1,x2,y2] and 'confidence'.
            frame: Current BGR frame (used by DeepSORT internally for appearance).

        Returns:
            List of tracked objects, each a dict with:
                - 'track_id': int (local per-camera ID)
                - 'bbox': [x1, y1, x2, y2]
                - 'confirmed': bool (whether track is confirmed by n_init hits)
        """
        if len(detections) == 0:
            # Still call update to age out stale tracks
            tracks = self.tracker.update_tracks([], frame=frame)
            return self._extract_tracks(tracks)

        # Convert detections to the format expected by deep_sort_realtime:
        # List of ([left, top, width, height], confidence, class_name)
        ds_detections = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            w = x2 - x1
            h = y2 - y1
            conf = det["confidence"]
            ds_detections.append(([x1, y1, w, h], conf, "person"))

        # Update tracks
        tracks = self.tracker.update_tracks(ds_detections, frame=frame)

        return self._extract_tracks(tracks)

    def _extract_tracks(self, tracks) -> list[dict]:
        """
        Extract confirmed tracks into a clean dict format.

        Args:
            tracks: Raw track objects from DeepSORT.

        Returns:
            List of track dicts.
        """
        results = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            if track.time_since_update > 1:
                # Skip tracks that haven't been updated recently
                continue

            # Get bounding box in ltrb format (left, top, right, bottom)
            ltrb = track.to_ltrb()
            bbox = [int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])]

            results.append({
                "track_id": track.track_id,
                "bbox": bbox,
                "confirmed": track.is_confirmed(),
            })

        return results

    def get_active_track_count(self) -> int:
        """Return the number of currently active (confirmed) tracks."""
        if hasattr(self.tracker, 'tracks'):
            return sum(1 for t in self.tracker.tracks if t.is_confirmed())
        return 0
