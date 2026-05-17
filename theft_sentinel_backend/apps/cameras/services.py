"""
Camera Feed Health Services

Observes feed availability WITHOUT modifying the stream pipeline.
Derives camera ONLINE/OFFLINE status from actual connectivity.

Dual-protocol:
  HTTP/HTTPS  → tested via requests.get()          (no OpenCV)
  RTSP/RTSPS  → tested via cv2.VideoCapture + read (CAP_FFMPEG)

URL is NEVER mutated — used exactly as stored in the database.

HARD 5-SECOND SLA: All cameras must be checked within 5 seconds total.
Uses parallel execution to ensure no single camera blocks others.
"""
import logging
import os
import cv2
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from urllib.parse import urlparse
from django.utils import timezone
from .models import Camera

logger = logging.getLogger(__name__)

# Hard 5-second SLA for the whole batch
MAX_TOTAL_CHECK_TIME_SECONDS = 5.0

# Environment-backed validation settings.
def _env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float, minimum: float = 0.1) -> float:
    try:
        return max(minimum, float(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


# Feed validation tuning. A stream is not considered live until at least one
# decoded frame passes validation.
VALIDATION_FRAME_COUNT = _env_int("CAMERA_VALIDATION_FRAME_COUNT", 5, minimum=3)
FRAME_READ_TIMEOUT_SECONDS = _env_float("CAMERA_FRAME_READ_TIMEOUT_SECONDS", 3.0)
FRAME_VALIDATION_DELAY_SECONDS = _env_float("CAMERA_FRAME_VALIDATION_DELAY_SECONDS", 0.15)

# Per-camera timeout - must remain under the batch SLA.
PER_CAMERA_TIMEOUT_SECONDS = FRAME_READ_TIMEOUT_SECONDS

CAMERA_FEED_UNAVAILABLE_MESSAGE = (
    "Camera feed is not available. Cannot turn on this camera."
)

_camera_transition_locks = {}
_camera_transition_locks_guard = threading.Lock()


def _get_camera_transition_lock(camera_id: str) -> threading.Lock:
    camera_id = str(camera_id)
    with _camera_transition_locks_guard:
        lock = _camera_transition_locks.get(camera_id)
        if lock is None:
            lock = threading.Lock()
            _camera_transition_locks[camera_id] = lock
        return lock


# ── Protocol helpers ────────────────────────────────────────────────────────

def _scheme(url: str) -> str:
    return urlparse(url).scheme.lower()


def _is_rtsp(url: str) -> bool:
    return _scheme(url) in ("rtsp", "rtsps")


def _is_http(url: str) -> bool:
    return _scheme(url) in ("http", "https")


# ── Per-protocol testers ────────────────────────────────────────────────────

def _is_valid_video_frame(frame) -> bool:
    """Return True only for decoded frames with non-empty pixel data."""
    if frame is None:
        return False

    if getattr(frame, "size", 0) <= 0:
        return False

    shape = getattr(frame, "shape", None)
    if not shape or len(shape) < 2:
        return False

    height, width = shape[:2]
    return height > 0 and width > 0


def _describe_invalid_frame(ret: bool, frame) -> str:
    if not ret:
        return "ret=False"
    if frame is None:
        return "frame=None"
    if getattr(frame, "size", 0) <= 0:
        return "frame has no pixel data"
    shape = getattr(frame, "shape", None)
    if not shape or len(shape) < 2:
        return f"invalid frame shape={shape}"
    height, width = shape[:2]
    return f"invalid dimensions width={width} height={height}"


def _set_capture_timeouts(cap, timeout_ms: int) -> None:
    buffer_size = getattr(cv2, "CAP_PROP_BUFFERSIZE", None)
    if buffer_size is not None:
        try:
            cap.set(buffer_size, 1)
        except Exception:
            pass

    for prop_name in ("CAP_PROP_OPEN_TIMEOUT_MSEC", "CAP_PROP_READ_TIMEOUT_MSEC"):
        prop = getattr(cv2, prop_name, None)
        if prop is not None:
            try:
                cap.set(prop, timeout_ms)
            except Exception:
                pass


def _open_rtsp_capture(stream_url: str, timeout_ms: int):
    timeout_params = []
    open_timeout = getattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC", None)
    read_timeout = getattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC", None)
    if open_timeout is not None:
        timeout_params.extend([open_timeout, timeout_ms])
    if read_timeout is not None:
        timeout_params.extend([read_timeout, timeout_ms])

    try:
        if timeout_params:
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG, timeout_params)
        else:
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
    except (TypeError, cv2.error):
        cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

    _set_capture_timeouts(cap, timeout_ms)
    return cap


def _read_validation_frames(cap, stream_url: str, protocol: str, timeout_s: float) -> bool:
    """
    Read several frames and accept the stream only after a real decoded frame.
    """
    deadline = time.monotonic() + timeout_s
    attempts_made = 0

    logger.info(
        "[health] Attempting to read validation frames from %s stream: %s",
        protocol,
        stream_url,
    )

    for attempt in range(1, VALIDATION_FRAME_COUNT + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.debug(
                "[health] Validation frame deadline reached before attempt %d/%d for %s",
                attempt,
                VALIDATION_FRAME_COUNT,
                stream_url,
            )
            break

        attempts_made = attempt
        try:
            ret, frame = cap.read()
        except Exception as exc:
            logger.debug(
                "[health] Validation frame read %d/%d raised for %s stream %s: %s",
                attempt,
                VALIDATION_FRAME_COUNT,
                protocol,
                stream_url,
                exc,
            )
            ret, frame = False, None

        if ret and _is_valid_video_frame(frame):
            height, width = frame.shape[:2]
            logger.info(
                "[health] Received valid video frame from %s stream: %s "
                "frame=%dx%d attempt=%d/%d",
                protocol,
                stream_url,
                width,
                height,
                attempt,
                VALIDATION_FRAME_COUNT,
            )
            return True

        logger.debug(
            "[health] Invalid validation frame %d/%d from %s stream %s: %s",
            attempt,
            VALIDATION_FRAME_COUNT,
            protocol,
            stream_url,
            _describe_invalid_frame(ret, frame),
        )

        if attempt < VALIDATION_FRAME_COUNT:
            remaining = deadline - time.monotonic()
            sleep_for = min(FRAME_VALIDATION_DELAY_SECONDS, max(0.0, remaining))
            if sleep_for > 0:
                time.sleep(sleep_for)

    logger.warning(
        "[health] No valid frames received from stream after %d/%d attempts: %s",
        attempts_made,
        VALIDATION_FRAME_COUNT,
        stream_url,
    )
    return False


def _test_http_feed(stream_url: str, timeout_s: float) -> bool:
    """
    Test an HTTP/HTTPS stream by sending a HEAD/GET request.
    Returns True if a 200 response with a media content-type is received.
    URL is used AS-IS — no endpoint suffix is added automatically.
    """
    try:
        # Try the stored URL first, then common video endpoint suffixes
        candidates = [stream_url]
        # Only append /video if the URL has no path segment beyond the port
        parsed = urlparse(stream_url)
        if not parsed.path or parsed.path == "/":
            candidates.append(stream_url.rstrip("/"))

        for url in candidates:
            try:
                resp = requests.get(url, stream=True, timeout=timeout_s)
                try:
                    if resp.status_code == 200:
                        ct = resp.headers.get("Content-Type", "")
                        if any(t in ct for t in ("multipart", "image", "video")):
                            logger.debug(
                                "[health] HTTP feed LIVE: camera url=%s ct=%s", url, ct
                            )
                            return True
                finally:
                    resp.close()
            except requests.exceptions.RequestException:
                continue
    except Exception as exc:
        logger.debug("[health] HTTP feed test error: %s", exc)
    return False


def _test_rtsp_feed(stream_url: str, timeout_s: float) -> bool:
    """
    Test an RTSP stream by opening it with CAP_FFMPEG and decoding frames.
    URL is used AS-IS — never converted or extended.

    isOpened() is ALWAYS checked before getBackendName().
    """
    timeout_ms = int(timeout_s * 1000)
    cap = None
    try:
        cap = _open_rtsp_capture(stream_url, timeout_ms)

        # ── CRITICAL: isOpened() BEFORE getBackendName() ───────────────────
        if not cap.isOpened():
            logger.debug("[health] RTSP feed DEAD (could not open): %s", stream_url)
            return False

        logger.info("[health] RTSP connection opened successfully: %s", stream_url)

        # Safe to call getBackendName() only after isOpened()
        backend = cap.getBackendName()
        if backend != "FFMPEG":
            logger.warning(
                "[health] Non-FFmpeg backend '%s' for RTSP health probe: %s",
                backend, stream_url,
            )

        return _read_validation_frames(cap, stream_url, "RTSP", timeout_s)

    except Exception as exc:
        logger.debug("[health] RTSP feed test exception for %s: %s", stream_url, exc)
        return False
    finally:
        if cap is not None:
            cap.release()


# ── Public interface ────────────────────────────────────────────────────────

def test_camera_feed(camera) -> bool:
    """
    Test whether a camera's feed is reachable and returning usable stream data.

    Routes to the correct protocol tester based on the URL scheme.
    The URL is used exactly as stored — NEVER mutated.
    """
    stream_url = camera.rtsp_url  # field name is legacy; may hold any URL
    timeout = PER_CAMERA_TIMEOUT_SECONDS

    if _is_http(stream_url):
        return _test_http_feed(stream_url, timeout)

    if _is_rtsp(stream_url):
        return _test_rtsp_feed(stream_url, timeout)

    logger.warning(
        "[health] Unknown protocol for camera %s: %s", camera.name, stream_url
    )
    return False


def _is_ai_ready() -> bool:
    try:
        from apps.ai_engine.services.ai_service import ai_service

        return ai_service.is_ready()
    except Exception as exc:
        logger.warning("[health] AI readiness check failed: %s", exc)
        return False


def _ensure_monitoring_started(camera) -> tuple[bool, str]:
    camera_id = str(camera.id)
    if not _is_ai_ready():
        return False, "AI service not ready. Models still loading."

    from apps.ai_engine.services.continuous_monitor import monitor_manager

    stats = monitor_manager.get_monitor_stats(camera_id)
    if stats and stats.get("is_running"):
        return True, "Monitor already running"

    if monitor_manager.start_monitor(camera_id, camera.rtsp_url):
        return True, "Started continuous monitoring"
    return False, "Failed to start monitoring"


def _stop_monitoring_and_stream(camera_id: str) -> bool:
    camera_id = str(camera_id)
    stopped_any = False

    try:
        from apps.ai_engine.services.continuous_monitor import monitor_manager

        stopped_any = monitor_manager.stop_monitor(camera_id) or stopped_any
    except Exception as exc:
        logger.error(
            "[health] Failed to stop AI monitor for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    try:
        from .stream_manager import stream_manager

        stopped_any = stream_manager.stop_stream(camera_id) or stopped_any
    except Exception as exc:
        logger.error(
            "[health] Failed to stop stream for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    return stopped_any


def cleanup_camera_runtime(camera_id: str) -> dict:
    """Stop transient runtime resources for a camera being disabled/deleted."""
    camera_id = str(camera_id)
    cleaned = {
        "camera_id": camera_id,
        "monitor_stopped": False,
        "stream_stopped": False,
        "tracking_cache_entries": 0,
        "sse_subscribers": 0,
    }

    try:
        from apps.ai_engine.services.continuous_monitor import monitor_manager

        cleaned["monitor_stopped"] = monitor_manager.stop_monitor(camera_id)
    except Exception as exc:
        logger.error(
            "[cleanup] Failed to stop monitor for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    try:
        from .stream_manager import stream_manager

        cleaned["stream_stopped"] = stream_manager.stop_stream(camera_id)
    except Exception as exc:
        logger.error(
            "[cleanup] Failed to stop stream for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    try:
        from apps.tracking.services import TrackingService

        cleaned["tracking_cache_entries"] = TrackingService.cleanup_camera_cache(camera_id)
    except Exception as exc:
        logger.error(
            "[cleanup] Failed to clean tracking cache for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    try:
        from apps.ai_engine.services.sse_registry import sse_registry

        cleaned["sse_subscribers"] = sse_registry.clear_camera(camera_id)
    except Exception as exc:
        logger.error(
            "[cleanup] Failed to clear SSE registry for camera %s: %s",
            camera_id,
            exc,
            exc_info=True,
        )

    logger.info("[cleanup] Camera runtime cleaned: %s", cleaned)
    return cleaned


def synchronize_camera_with_feed(
    camera,
    feed_live: bool,
    *,
    source: str = "health",
    start_monitoring: bool = True,
    require_monitoring: bool = False,
) -> tuple[bool, str, bool]:
    """
    Apply a feed-derived ON/OFF state and monitoring lifecycle.

    Returns:
        (success, message, db_updated)
    """
    now = timezone.now()
    camera_id = str(camera.id)

    lock = _get_camera_transition_lock(camera_id)
    with lock:
        db_fields = []
        monitor_ok = True
        monitor_message = "Monitoring not requested"

        if feed_live:
            status_was_offline = camera.status != "ONLINE"
            if start_monitoring:
                monitor_ok, monitor_message = _ensure_monitoring_started(camera)
                if require_monitoring and not monitor_ok:
                    logger.warning(
                        "[%s] Camera %s feed live but monitor start failed: %s",
                        source,
                        camera.name,
                        monitor_message,
                    )
                    return False, monitor_message, False

            if camera.status != "ONLINE":
                camera.status = "ONLINE"
                db_fields.append("status")

            if hasattr(camera, "last_feed_timestamp"):
                last_seen = camera.last_feed_timestamp
                should_touch_feed = (
                    status_was_offline
                    or last_seen is None
                    or (now - last_seen).total_seconds() >= 30
                )
                if should_touch_feed:
                    camera.last_feed_timestamp = now
                    db_fields.append("last_feed_timestamp")

            if start_monitoring and monitor_ok and not camera.ai_monitoring_enabled:
                camera.ai_monitoring_enabled = True
                db_fields.append("ai_monitoring_enabled")

            if db_fields:
                camera.save(update_fields=sorted(set(db_fields)))
                logger.info(
                    "[%s] Camera %s marked ONLINE after receiving valid video frames; monitoring=%s",
                    source,
                    camera.name,
                    "running" if monitor_ok else "not ready",
                )
                return True, monitor_message, True
            return True, monitor_message, False

        runtime_stopped = _stop_monitoring_and_stream(camera_id)

        if camera.status != "OFFLINE":
            camera.status = "OFFLINE"
            db_fields.append("status")
        if camera.ai_monitoring_enabled:
            camera.ai_monitoring_enabled = False
            db_fields.append("ai_monitoring_enabled")

        if db_fields:
            camera.save(update_fields=sorted(set(db_fields)))
            logger.info(
                "[%s] Camera %s marked OFFLINE because no video frames were received; runtime_stopped=%s",
                source,
                camera.name,
                runtime_stopped,
            )
            return True, "Camera feed unavailable; monitoring stopped", True
        return True, "Camera feed unavailable; already offline", False


def update_camera_status_from_feed(camera) -> bool:
    """
    Update camera status and monitoring state based on actual feed state.
    Returns True if the DB was updated.
    """
    feed_live = test_camera_feed(camera)
    _, _, updated = synchronize_camera_with_feed(
        camera,
        feed_live,
        source="health",
        start_monitoring=True,
        require_monitoring=False,
    )
    return updated


def turn_camera_on_after_feed_check(camera) -> tuple[bool, str, bool]:
    """Manual ON transition: validate feed first, then start monitoring."""
    if not test_camera_feed(camera):
        return False, CAMERA_FEED_UNAVAILABLE_MESSAGE, False

    return synchronize_camera_with_feed(
        camera,
        True,
        source="manual",
        start_monitoring=True,
        require_monitoring=True,
    )


def turn_camera_off(camera) -> tuple[bool, str, bool]:
    """Manual OFF transition: stop monitoring and mark camera offline."""
    return synchronize_camera_with_feed(
        camera,
        False,
        source="manual",
        start_monitoring=False,
        require_monitoring=False,
    )


def check_all_camera_feeds() -> dict:
    """
    Check all cameras in parallel and update their status.
    Hard 5-second SLA for the entire batch.
    """
    start_time = time.time()
    now = timezone.now()

    cameras = list(Camera.objects.all())
    total = len(cameras)

    if total == 0:
        return {"checked": 0, "updated": 0, "timestamp": now, "elapsed_seconds": 0.0}

    max_workers = min(total, 10)
    cameras_checked = 0
    cameras_updated = 0

    def _probe(cam):
        try:
            return test_camera_feed(cam)
        except Exception as exc:
            logger.error(
                "[health] Error checking camera %s: %s", cam.name, exc, exc_info=True
            )
            return False

    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {executor.submit(_probe, cam): cam for cam in cameras}
    try:
        done, pending = wait(futures, timeout=MAX_TOTAL_CHECK_TIME_SECONDS)

        for future in done:
            cam = futures[future]
            cameras_checked += 1
            try:
                feed_live = future.result(timeout=0.1)
                _, _, updated = synchronize_camera_with_feed(
                    cam,
                    feed_live,
                    source="health",
                    start_monitoring=True,
                    require_monitoring=False,
                )
                if updated:
                    cameras_updated += 1
            except Exception as exc:
                logger.error(
                    "[health] Result error for camera %s: %s", cam.name, exc
                )
                _, _, updated = synchronize_camera_with_feed(
                    cam,
                    False,
                    source="health",
                    start_monitoring=False,
                    require_monitoring=False,
                )
                if updated:
                    cameras_updated += 1

        for future in pending:
            cam = futures[future]
            future.cancel()
            logger.warning(
                "[health] Feed probe timed out for camera %s; marking unavailable",
                cam.name,
            )
            _, _, updated = synchronize_camera_with_feed(
                cam,
                False,
                source="health",
                start_monitoring=False,
                require_monitoring=False,
            )
            if updated:
                cameras_updated += 1
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    elapsed = time.time() - start_time

    if cameras_checked < total:
        logger.warning(
            "[health] SLA exceeded: only %d/%d cameras checked in %.2fs",
            cameras_checked, total, elapsed,
        )

    stats = {
        "checked": cameras_checked,
        "updated": cameras_updated,
        "timestamp": now,
        "elapsed_seconds": round(elapsed, 2),
    }

    if elapsed > MAX_TOTAL_CHECK_TIME_SECONDS:
        logger.warning(
            "[health] Batch check exceeded 5s SLA: %.2fs (%d/%d cameras)",
            elapsed, cameras_checked, total,
        )
    else:
        logger.debug(
            "[health] Batch check OK: %.2fs | %d cameras | %d updated",
            elapsed, cameras_checked, cameras_updated,
        )

    return stats
