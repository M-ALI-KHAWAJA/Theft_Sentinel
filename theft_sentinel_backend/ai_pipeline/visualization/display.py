"""
Visualization Module — updated for theft detection.

Bounding box color now reflects X3D theft score:
  RED    → theft detected  (score >= THEFT_THRESHOLD)
  ORANGE → suspicious      (score >= SUSPICIOUS_THRESHOLD)
  GREEN  → normal          (score < SUSPICIOUS_THRESHOLD)
  GREY   → not yet scored  (buffer still filling)

Label shows: Global ID | Local ID | theft score (when available)
"""

import cv2
import numpy as np
from config.config import Config


# 20-color palette for global IDs (BGR)
COLORS = [
    (0, 255, 0),    (255, 0, 0),    (0, 0, 255),    (255, 255, 0),
    (0, 255, 255),  (255, 0, 255),  (128, 255, 0),  (255, 128, 0),
    (0, 128, 255),  (128, 0, 255),  (255, 255, 128),(128, 255, 255),
    (255, 128, 255),(0, 200, 100),  (200, 100, 0),  (100, 0, 200),
    (200, 200, 0),  (0, 200, 200),  (200, 0, 200),  (100, 200, 100),
]

# Fixed alert colors (override palette when theft/suspicious)
COLOR_THEFT      = (0,   0,   255)   # Red
COLOR_SUSPICIOUS = (0,   165, 255)   # Orange
COLOR_NORMAL     = (0,   255, 0)     # Green
COLOR_UNKNOWN    = (180, 180, 180)   # Grey (no score yet)


def get_palette_color(global_id: int) -> tuple:
    return COLORS[global_id % len(COLORS)]


def get_theft_color(theft_score: float | None) -> tuple:
    """Return bbox color based on X3D theft probability."""
    if theft_score is None:
        return COLOR_UNKNOWN
    if theft_score >= Config.X3D_THEFT_THRESHOLD:
        return COLOR_THEFT
    if theft_score >= Config.X3D_SUSPICIOUS_THRESHOLD:
        return COLOR_SUSPICIOUS
    return COLOR_NORMAL


class Visualizer:
    """Multi-camera visualization with theft-aware overlays."""

    def __init__(self):
        self.font        = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale  = Config.VIS_FONT_SCALE
        self.thickness   = Config.VIS_BBOX_THICKNESS
        self.window_width  = Config.VIS_WINDOW_WIDTH
        self.window_height = Config.VIS_WINDOW_HEIGHT

    # ── main draw method ──────────────────────────────────────────────────────

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: list[dict],
        camera_id: int,
        theft_scores: dict[int, float] | None = None,
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on a frame.

        Args:
            frame:        BGR frame.
            detections:   List of dicts with 'bbox', 'track_id', 'global_id',
                          'match_score'.
            camera_id:    Camera identifier (for label).
            theft_scores: Dict mapping global_id → theft probability.
                          Pass None or empty if X3D has not scored yet.

        Returns:
            Annotated frame copy.
        """
        annotated = frame.copy()
        theft_scores = theft_scores or {}

        # Camera label
        cv2.putText(
            annotated, f"Camera {camera_id}",
            (10, 30), self.font, 0.8, (255, 255, 255), 2, cv2.LINE_AA,
        )

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            track_id  = det.get("track_id", -1)
            global_id = det.get("global_id", -1)
            match_score = det.get("match_score", 0.0)

            # Theft score for this global identity
            theft_score = theft_scores.get(global_id)

            # Choose color
            color = get_theft_color(theft_score)

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, self.thickness)

            # Build label
            label_parts = []
            if Config.VIS_SHOW_GLOBAL_ID and global_id > 0:
                label_parts.append(f"G:{global_id}")
            if Config.VIS_SHOW_LOCAL_ID:
                label_parts.append(f"L:{track_id}")
            if theft_score is not None:
                label_parts.append(f"T:{theft_score:.0%}")
            elif match_score > 0:
                label_parts.append(f"M:{match_score:.2f}")

            label = " | ".join(label_parts)

            # Theft alert badge above box
            if theft_score is not None and theft_score >= Config.X3D_THEFT_THRESHOLD:
                alert = "! THEFT !"
                (aw, ah), _ = cv2.getTextSize(alert, self.font, 0.7, 2)
                cx = (x1 + x2) // 2 - aw // 2
                cv2.rectangle(annotated, (cx - 4, y1 - ah - 30),
                              (cx + aw + 4, y1 - 18), COLOR_THEFT, -1)
                cv2.putText(annotated, alert, (cx, y1 - 20),
                            self.font, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

            if label:
                (tw, th), bl = cv2.getTextSize(label, self.font, self.font_scale, 1)
                cv2.rectangle(
                    annotated,
                    (x1, y1 - th - bl - 6),
                    (x1 + tw + 4, y1),
                    color, -1,
                )
                cv2.putText(
                    annotated, label,
                    (x1 + 2, y1 - bl - 4),
                    self.font, self.font_scale, (0, 0, 0), 1, cv2.LINE_AA,
                )

        return annotated

    # ── tiled display ─────────────────────────────────────────────────────────

    def create_tiled_display(self, frames: dict[int, np.ndarray]) -> np.ndarray:
        """Arrange camera frames in a grid."""
        if not frames:
            return np.zeros((self.window_height, self.window_width, 3), dtype=np.uint8)

        n = len(frames)
        if n <= 1:   cols, rows = 1, 1
        elif n <= 2: cols, rows = 2, 1
        elif n <= 4: cols, rows = 2, 2
        elif n <= 6: cols, rows = 3, 2
        elif n <= 9: cols, rows = 3, 3
        else:
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))

        tw = self.window_width  // cols
        th = self.window_height // rows
        canvas = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)

        for idx, cam_id in enumerate(sorted(frames)):
            row, col = divmod(idx, cols)
            tile = cv2.resize(frames[cam_id], (tw, th))
            canvas[row*th:(row+1)*th, col*tw:(col+1)*tw] = tile

        return canvas

    # ── stats overlay ─────────────────────────────────────────────────────────

    def draw_stats_overlay(self, frame: np.ndarray, stats: dict) -> np.ndarray:
        """Draw FPS and identity stats at the bottom of the frame."""
        annotated = frame.copy()
        h = annotated.shape[0]
        y = h - 20
        lh = 22

        lines = [
            f"Global IDs: {stats.get('total_identities', 0)}",
            f"Active Tracks: {stats.get('active_tracks', 0)}",
            f"FAISS Index: {stats.get('faiss_size', 0)}",
            f"Theft Alerts: {stats.get('theft_alerts', 0)}",
            f"FPS: {stats.get('fps', 0.0):.1f}",
        ]

        for line in reversed(lines):
            cv2.putText(annotated, line, (10, y),
                        self.font, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
            y -= lh

        return annotated
