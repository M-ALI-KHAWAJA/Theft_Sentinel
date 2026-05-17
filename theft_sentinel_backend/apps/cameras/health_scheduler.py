import atexit
import logging
import os
import sys
import threading
import time

from .services import check_all_camera_feeds

logger = logging.getLogger(__name__)


class CameraFeedHealthScheduler:
    """In-process camera feed health scheduler."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._interval = 5

    def start(self, interval: int = 5) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._interval = max(1, int(interval))
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._loop,
                daemon=True,
                name="camera-feed-health-checker",
            )
            self._thread.start()
            atexit.register(self.stop)
            logger.info(
                "[health] Camera feed health scheduler started interval=%ss",
                self._interval,
            )
            return True

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        logger.info("[health] Camera feed health scheduler stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            started_at = time.time()
            try:
                check_all_camera_feeds()
            except Exception as exc:
                logger.error(
                    "[health] Scheduled feed check failed: %s",
                    exc,
                    exc_info=True,
                )

            elapsed = time.time() - started_at
            sleep_for = max(0.0, self._interval - elapsed)
            if self._stop_event.wait(timeout=sleep_for):
                break


def should_start_health_scheduler() -> bool:
    enabled = os.environ.get("CAMERA_FEED_HEALTH_CHECKER_ENABLED", "true").lower()
    if enabled in {"0", "false", "no", "off"}:
        return False

    argv = " ".join(sys.argv).lower()
    executable = os.path.basename(sys.argv[0]).lower() if sys.argv else ""

    if "runserver" in argv:
        return os.environ.get("RUN_MAIN") == "true" or "--noreload" in argv

    return executable in {"gunicorn", "uvicorn", "daphne"} or "gunicorn" in executable


health_scheduler = CameraFeedHealthScheduler()
