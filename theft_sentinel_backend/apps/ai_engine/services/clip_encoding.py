"""Encode in-memory frames to a temporary H.264-friendly MP4 via OpenCV."""
import logging
from typing import Any, Sequence

import cv2

logger = logging.getLogger(__name__)

# Maximum width for uploaded clips (keeps Cloudinary storage small)
_MAX_WIDTH = 1280


def _best_fourcc():
    """Return the best available fourcc for browser-compatible MP4."""
    # avc1 = H.264, universally supported in browsers
    for codec in ("avc1", "H264", "X264", "mp4v"):
        cc = cv2.VideoWriter_fourcc(*codec)
        if cc != -1:
            return cc
    return cv2.VideoWriter_fourcc(*"mp4v")


def write_frames_to_mp4(frames: Sequence[Any], out_path: str, fps: float) -> bool:
    if not frames:
        return False
    fps = max(8.0, min(float(fps), 60.0))
    h, w = frames[0].shape[:2]

    # Downscale wide frames to keep file size manageable
    if w > _MAX_WIDTH:
        scale = _MAX_WIDTH / w
        w = _MAX_WIDTH
        h = int(h * scale)

    fourcc = _best_fourcc()
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    if not writer.isOpened():
        logger.error("VideoWriter failed to open for %s", out_path)
        return False
    try:
        for frame in frames:
            f = frame
            # Resize if needed
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
