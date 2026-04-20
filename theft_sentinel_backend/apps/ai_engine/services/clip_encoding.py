"""Encode in-memory frames to a temporary H.264-friendly MP4 via OpenCV."""
import logging
from typing import Any, Sequence

import cv2

logger = logging.getLogger(__name__)


def write_frames_to_mp4(frames: Sequence[Any], out_path: str, fps: float) -> bool:
    if not frames:
        return False
    fps = max(8.0, min(float(fps), 60.0))
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not writer.isOpened():
        logger.error("VideoWriter failed to open for %s", out_path)
        return False
    try:
        for frame in frames:
            f = frame
            if f.shape[0] != h or f.shape[1] != w:
                f = cv2.resize(f, (w, h))
            if f.ndim == 2:
                f = cv2.cvtColor(f, cv2.COLOR_GRAY2BGR)
            elif f.shape[2] == 4:
                f = cv2.cvtColor(f, cv2.COLOR_BGRA2BGR)
            writer.write(f)
    finally:
        writer.release()
    return True
