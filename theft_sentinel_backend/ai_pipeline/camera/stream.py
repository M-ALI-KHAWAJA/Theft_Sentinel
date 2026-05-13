"""
Camera Stream Handler Module.

Provides threaded camera stream readers for:
    - Video files
    - RTSP streams
    - USB/webcam devices

Each camera runs in its own thread for async, non-blocking frame capture.
"""

import cv2
import time
import threading
import numpy as np
from config.config import Config


class CameraStream:
    """
    Threaded camera stream reader.

    Continuously captures frames in a background thread.
    The latest frame is always available via get_frame().
    """

    def __init__(self, source, camera_id: int):
        """
        Initialize a camera stream.

        Args:
            source: Video file path (str), RTSP URL (str), or device index (int).
            camera_id: Unique identifier for this camera.
        """
        self.source = source
        self.camera_id = camera_id
        self.cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._frame_count = 0
        self._fps = 0.0
        self._last_fps_time = time.time()
        self._fps_frame_count = 0

    def start(self) -> bool:
        """
        Open the video source and start the capture thread.

        Returns:
            True if the stream opened successfully, False otherwise.
        """
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            print(f"[Camera {self.camera_id}] ERROR: Cannot open source: {self.source}")
            return False

        # Get source properties
        src_fps = self.cap.get(cv2.CAP_PROP_FPS)
        src_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        src_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"[Camera {self.camera_id}] Opened: {self.source}")
        print(f"  Resolution: {src_width}x{src_height}, FPS: {src_fps:.1f}, "
              f"Total frames: {total_frames}")

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        return True

    def _capture_loop(self):
        """Background thread: continuously read frames from the source."""
        target_interval = 1.0 / Config.TARGET_FPS if Config.TARGET_FPS > 0 else 0

        while self._running:
            start_time = time.time()

            ret, frame = self.cap.read()

            if not ret:
                # For video files, loop back to the beginning
                if isinstance(self.source, str) and not self.source.startswith("rtsp"):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print(f"[Camera {self.camera_id}] Stream ended or lost connection")
                    time.sleep(1.0)
                    # Try to reconnect for RTSP
                    self.cap.release()
                    self.cap = cv2.VideoCapture(self.source)
                    continue

            # Resize for consistent processing
            if frame.shape[1] != Config.FRAME_WIDTH or frame.shape[0] != Config.FRAME_HEIGHT:
                frame = cv2.resize(frame, (Config.FRAME_WIDTH, Config.FRAME_HEIGHT))

            with self._lock:
                self._frame = frame
                self._frame_count += 1

            # FPS calculation
            self._fps_frame_count += 1
            now = time.time()
            if now - self._last_fps_time >= 1.0:
                self._fps = self._fps_frame_count / (now - self._last_fps_time)
                self._fps_frame_count = 0
                self._last_fps_time = now

            # Rate limiting
            elapsed = time.time() - start_time
            if elapsed < target_interval:
                time.sleep(target_interval - elapsed)

    def get_frame(self) -> tuple[bool, np.ndarray | None]:
        """
        Get the latest captured frame.

        Returns:
            (success, frame) where frame is a BGR numpy array or None.
        """
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def get_fps(self) -> float:
        """Return the current capture FPS."""
        return self._fps

    def get_frame_count(self) -> int:
        """Return the total number of frames captured."""
        return self._frame_count

    def stop(self):
        """Stop the capture thread and release the video source."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        if self.cap is not None:
            self.cap.release()
        print(f"[Camera {self.camera_id}] Stopped")

    def is_running(self) -> bool:
        """Check if the stream is still active."""
        return self._running


class MultiCameraManager:
    """
    Manages multiple camera streams.

    Provides a unified interface to start/stop all cameras
    and retrieve frames from any camera.
    """

    def __init__(self):
        """Initialize the multi-camera manager."""
        self.cameras: dict[int, CameraStream] = {}

    def add_camera(self, source, camera_id: int) -> bool:
        """
        Add and start a camera stream.

        Args:
            source: Video source (file path, RTSP URL, or device index).
            camera_id: Unique camera identifier.

        Returns:
            True if the camera started successfully.
        """
        stream = CameraStream(source, camera_id)
        if stream.start():
            self.cameras[camera_id] = stream
            return True
        return False

    def get_frame(self, camera_id: int) -> tuple[bool, np.ndarray | None]:
        """Get the latest frame from a specific camera."""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame()
        return False, None

    def get_all_frames(self) -> dict[int, np.ndarray]:
        """
        Get the latest frame from all cameras.

        Returns:
            Dict mapping camera_id → frame (only includes cameras with valid frames).
        """
        frames = {}
        for cam_id, stream in self.cameras.items():
            ret, frame = stream.get_frame()
            if ret and frame is not None:
                frames[cam_id] = frame
        return frames

    def stop_all(self):
        """Stop all camera streams."""
        for stream in self.cameras.values():
            stream.stop()
        self.cameras.clear()
        print("[MultiCameraManager] All cameras stopped")

    def get_camera_ids(self) -> list[int]:
        """Return list of active camera IDs."""
        return list(self.cameras.keys())

    def is_any_running(self) -> bool:
        """Check if at least one camera is still running."""
        return any(s.is_running() for s in self.cameras.values())
