"""
Camera Feed Health Services

OBSERVES feed behavior WITHOUT modifying the feed pipeline.
Derives camera ONLINE/OFFLINE status from actual feed availability.

HARD 5-SECOND SLA: All cameras must be checked within 5 seconds total.
Uses parallel execution to ensure no single camera blocks others.
"""
import logging
import cv2
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from django.utils import timezone
from datetime import timedelta
from .models import Camera

logger = logging.getLogger(__name__)

# Feed timeout: If no feed activity for 10 seconds, camera is OFFLINE
FEED_TIMEOUT_SECONDS = 10

# Hard 5-second SLA: All cameras must be checked within this time
MAX_TOTAL_CHECK_TIME_SECONDS = 5.0

# Per-camera timeout: Each camera check must complete within this time
PER_CAMERA_TIMEOUT_SECONDS = 2.0


def test_camera_feed(camera):
    """
    Test if camera feed is actually accessible and working.
    This is the SINGLE SOURCE OF TRUTH for camera online/offline status.
    
    OBSERVES feed WITHOUT modifying the pipeline.
    Uses the same methods as the pipeline (HTTP requests, OpenCV) but externally.
    
    HARD TIMEOUT: Must complete within PER_CAMERA_TIMEOUT_SECONDS (2 seconds).
    """
    start_time = time.time()
    
    try:
        stream_url = camera.rtsp_url
        
        # For HTTP/HTTPS streams, test direct connection (with timeout)
        if stream_url.startswith('http://') or stream_url.startswith('https://'):
            possible_endpoints = ['/video', '/videofeed', '/shot.jpg', '']
            for endpoint in possible_endpoints:
                # Check if we've exceeded per-camera timeout
                if time.time() - start_time > PER_CAMERA_TIMEOUT_SECONDS:
                    logger.debug(f"⏱️ Camera {camera.name} feed test timed out (HTTP)")
                    return False
                    
                try:
                    test_url = stream_url.rstrip('/') + endpoint
                    # Use shorter timeout to ensure we meet per-camera SLA
                    response = requests.get(
                        test_url, 
                        timeout=PER_CAMERA_TIMEOUT_SECONDS, 
                        stream=True
                    )
                    if response.status_code == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'multipart' in content_type or 'image' in content_type or 'video' in content_type:
                            logger.debug(f"✅ Camera {camera.name} feed is LIVE (HTTP: {test_url})")
                            return True
                except (requests.exceptions.Timeout, requests.exceptions.RequestException):
                    continue
        
        # For RTSP or if HTTP failed, use OpenCV (with timeout)
        # Check if we've exceeded per-camera timeout
        if time.time() - start_time > PER_CAMERA_TIMEOUT_SECONDS:
            logger.debug(f"⏱️ Camera {camera.name} feed test timed out (before OpenCV)")
            return False
            
        try:
            processed_url = stream_url
            if stream_url.startswith('http://') and not any(x in stream_url for x in ['/video', '/videofeed', '/shot.jpg']):
                processed_url = stream_url.rstrip('/') + '/video'

            # Convert timeout to milliseconds
            timeout_ms = int(PER_CAMERA_TIMEOUT_SECONDS * 1000)

            # RTSP transport env-vars are initialised globally in apps/ai_engine/apps.py.
            # Log here to confirm they are visible in this process/thread before open.
            logger.warning(
                f"[RTSP DEBUG] PID={os.getpid()} | health-probe | camera={camera.name} | "
                f"OPENCV_FFMPEG_CAPTURE_OPTIONS="
                f"{os.environ.get('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'NOT SET')}"
            )

            # Explicit CAP_FFMPEG so OPENCV_FFMPEG_CAPTURE_OPTIONS (UDP transport)
            # is honoured. Without this flag, Windows probes MSMF first which sends a
            # TCP RTSP SETUP to MediaMTX before FFmpeg ever sees the env-var.
            cap = cv2.VideoCapture(processed_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout_ms)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout_ms)

            # Log backend + warn if not FFmpeg
            backend = cap.getBackendName()
            logger.warning(
                f"[RTSP DEBUG] camera={camera.name} | Backend={backend} | "
                f"PID={os.getpid()}"
            )
            if backend != "FFMPEG":
                logger.warning(
                    f"⚠️ Non-FFmpeg backend detected for health probe of "
                    f"{camera.name}: {backend} — transport may default to TCP"
                )
            else:
                logger.debug(
                    f"📡 Health probe backend=FFMPEG (UDP) for {camera.name}: {processed_url}"
                )

            if not cap.isOpened():
                logger.debug(f"❌ Camera {camera.name} feed is DEAD (cannot open: {processed_url})")
                return False

            # Check timeout before reading frame
            if time.time() - start_time > PER_CAMERA_TIMEOUT_SECONDS:
                cap.release()
                logger.debug(f"⏱️ Camera {camera.name} feed test timed out (OpenCV open)")
                return False
            
            ret, frame = cap.read()
            cap.release()
            
            # Final timeout check
            if time.time() - start_time > PER_CAMERA_TIMEOUT_SECONDS:
                logger.debug(f"⏱️ Camera {camera.name} feed test timed out (OpenCV read)")
                return False
            
            if ret and frame is not None:
                logger.debug(f"✅ Camera {camera.name} feed is LIVE (RTSP/OpenCV)")
                return True
            else:
                logger.debug(f"❌ Camera {camera.name} feed is DEAD (no frame received)")
                return False
                
        except Exception as e:
            logger.debug(f"❌ Camera {camera.name} feed test failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.exception(f"Error testing camera feed for {camera.name}: {e}")
        return False


def update_camera_status_from_feed(camera):
    """
    Update camera status based on actual feed state.
    This is the authoritative source of truth.
    
    OBSERVES feed WITHOUT modifying the pipeline.
    """
    feed_is_live = test_camera_feed(camera)
    now = timezone.now()
    
    if feed_is_live:
        if camera.status != 'ONLINE':
            camera.status = 'ONLINE'
            if hasattr(camera, 'last_feed_timestamp'):
                camera.last_feed_timestamp = now
            camera.save(update_fields=['status'])
            logger.info(f"📹 Camera {camera.name} marked ONLINE (feed confirmed live)")
            return True
        else:
            # Already online, just update timestamp if field exists
            if hasattr(camera, 'last_feed_timestamp'):
                camera.last_feed_timestamp = now
                camera.save(update_fields=['last_feed_timestamp'])
            return False
    else:
        if camera.status != 'OFFLINE':
            camera.status = 'OFFLINE'
            camera.save(update_fields=['status'])
            logger.info(f"📹 Camera {camera.name} marked OFFLINE (feed confirmed dead)")
            return True
        return False


def check_all_camera_feeds():
    """
    Check all cameras and update their status based on actual feed state.
    This should be called periodically (e.g., every 5 seconds).
    
    HARD 5-SECOND SLA: All cameras must be checked within MAX_TOTAL_CHECK_TIME_SECONDS.
    Uses parallel execution to ensure no single camera blocks others.
    
    OBSERVES feeds WITHOUT modifying the pipeline.
    """
    start_time = time.time()
    now = timezone.now()
    cameras_checked = 0
    cameras_updated = 0
    
    # Get all cameras
    cameras = list(Camera.objects.all())
    total_cameras = len(cameras)
    
    if total_cameras == 0:
        logger.debug("No cameras to check")
        return {
            'checked': 0,
            'updated': 0,
            'timestamp': now,
            'elapsed_seconds': 0.0
        }
    
    # Use ThreadPoolExecutor for parallel execution
    # Limit max_workers to prevent resource exhaustion
    max_workers = min(total_cameras, 10)  # Check up to 10 cameras in parallel
    
    def check_single_camera(camera):
        """Check a single camera and return update status"""
        try:
            return update_camera_status_from_feed(camera)
        except Exception as e:
            logger.error(f"Error checking camera {camera.name}: {e}", exc_info=True)
            return False
    
    # Execute camera checks in parallel with timeout
    updated_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all camera checks
        future_to_camera = {
            executor.submit(check_single_camera, camera): camera 
            for camera in cameras
        }
        
        # Collect results with timeout
        for future in as_completed(future_to_camera, timeout=MAX_TOTAL_CHECK_TIME_SECONDS):
            camera = future_to_camera[future]
            cameras_checked += 1
            
            try:
                if future.result(timeout=0.1):  # Quick result retrieval
                    cameras_updated += 1
            except Exception as e:
                logger.error(f"Error getting result for camera {camera.name}: {e}")
                # Mark camera as offline if check failed
                if camera.status != 'OFFLINE':
                    camera.status = 'OFFLINE'
                    camera.save(update_fields=['status'])
                    cameras_updated += 1
    
    elapsed = time.time() - start_time
    
    # Handle any cameras that didn't complete in time
    if cameras_checked < total_cameras:
        remaining_cameras = total_cameras - cameras_checked
        logger.warning(
            f"⚠️ Camera check exceeded 5-second SLA: "
            f"{remaining_cameras} cameras not checked in time. "
            f"Elapsed: {elapsed:.2f}s"
        )
        # Mark remaining cameras as offline (timeout = feed unavailable)
        for camera in cameras:
            if cameras_checked < total_cameras:
                if camera.status != 'OFFLINE':
                    camera.status = 'OFFLINE'
                    camera.save(update_fields=['status'])
                    cameras_updated += 1
                cameras_checked += 1
    
    stats = {
        'checked': cameras_checked,
        'updated': cameras_updated,
        'timestamp': now,
        'elapsed_seconds': round(elapsed, 2)
    }
    
    if elapsed > MAX_TOTAL_CHECK_TIME_SECONDS:
        logger.warning(
            f"⚠️ Camera feed check exceeded 5-second SLA: {elapsed:.2f}s "
            f"({cameras_checked}/{total_cameras} cameras checked)"
        )
    else:
        logger.debug(
            f"✅ All camera feed checks completed within SLA: {elapsed:.2f}s "
            f"({cameras_checked}/{total_cameras} cameras, {cameras_updated} updated)"
        )
    
    return stats

