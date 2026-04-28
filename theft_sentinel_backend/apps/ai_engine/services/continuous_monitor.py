"""
Continuous Camera Monitoring Service
Runs your existing AI pipeline continuously on camera streams
Stores results in database for frontend to read in real-time
"""

import os
os.environ["OPENH264_LIBRARY"] = r"Z:\FYP\fyp_application\env\Scripts\openh264-1.8.0-win64.dll"
import cv2
import tempfile
import time
import threading
import logging
from collections import deque
from typing import Dict, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """
    Runs continuous AI monitoring on camera streams
    Processes frames at full FPS (15-30) instead of 2-second intervals
    """
    
    # Maximum rate at which the SSE callback is fired (frames per second).
    # Keeps bandwidth low on cloud deployments while still giving smooth overlays.
    _SSE_MAX_FPS: float = 10.0

    def __init__(self, camera_id: str, rtsp_url: str, callback=None):
        """
        Args:
            camera_id: Camera database ID
            rtsp_url: Camera RTSP/HTTP stream URL
            callback: Optional function to call with results (for real-time updates)
        """
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.callback = callback

        self.is_running = False
        self.thread = None
        self.capture_thread = None
        self.cap = None
        self.latest_frame = None

        # Stats
        self.frames_processed = 0
        self.frames_captured = 0
        self.start_time = None
        self.last_result = None
        self.error_count = 0

        # Rolling frame buffer (~5s at 30 FPS) for theft clip generation
        self._frame_buffer = deque(maxlen=150)

        # Throttle SSE / callback publishing to _SSE_MAX_FPS
        self._last_callback_time: float = 0.0
        
        # 5-second cooldown for alerting
        self.last_alert_time: float = 0.0
    
    def start(self):
        """Start continuous monitoring in background thread"""
        if self.is_running:
            logger.warning(f"Monitor already running for camera {self.camera_id}")
            return False
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"🎥 Started continuous monitoring for camera {self.camera_id}")
        return True
    
    def stop(self):
        """Stop continuous monitoring"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
        if self.thread:
            self.thread.join(timeout=5.0)
        if self.cap:
            self.cap.release()
        logger.info(f"🛑 Stopped monitoring for camera {self.camera_id}")
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            fps = self.frames_processed / elapsed if elapsed > 0 else 0
            capture_fps = self.frames_captured / elapsed if elapsed > 0 else 0
        else:
            fps = 0
            capture_fps = 0
            elapsed = 0
        
        return {
            'camera_id': self.camera_id,
            'is_running': self.is_running,
            'frames_processed': self.frames_processed,
            'frames_captured': self.frames_captured,
            'fps': round(fps, 2),
            'capture_fps': round(capture_fps, 2),
            'elapsed_seconds': round(elapsed, 2),
            'error_count': self.error_count,
            'last_result': self.last_result,
        }
    
    def _capture_loop(self):
        """Dedicated thread to read frames at full camera FPS"""
        processed_url = self._prepare_url(self.rtsp_url)
        self.cap = cv2.VideoCapture(processed_url)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open stream: {processed_url}")
            self.is_running = False
            return
            
        logger.info(f"✅ Stream opened successfully for camera {self.camera_id}")
        
        while self.is_running:
            try:
                ret, raw_frame = self.cap.read()
                
                if not ret or raw_frame is None or getattr(raw_frame, "size", 0) == 0:
                    logger.warning(f"Failed to read frame from camera {self.camera_id}")
                    self.error_count += 1
                    
                    # Reconnect after too many errors
                    if self.error_count > 10:
                        logger.info("Too many errors, reconnecting...")
                        self.cap.release()
                        time.sleep(2)
                        self.cap = cv2.VideoCapture(processed_url)
                        self.error_count = 0
                    
                    time.sleep(0.1)
                    continue
                
                # Downscale instantly. 640x480 is plenty for X3D inference and Cloudinary clips.
                # This reduces memory from 6.2MB per frame to 0.9MB.
                frame = cv2.resize(raw_frame, (640, 480))
                
                # Explicitly delete the raw 1080p array to free memory
                del raw_frame 

                # Reset error count on success
                self.error_count = 0
                self.frames_captured += 1
                self.latest_frame = frame.copy()
                self._frame_buffer.append(self.latest_frame)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {str(e)}", exc_info=True)
                self.error_count += 1
                time.sleep(0.5)

    def _monitor_loop(self):
        """Main inference loop - runs at AI processing speed"""
        from .inference_runner import InferenceRunner
        from ..utils.frame_utils import capture_frame_from_rtsp
        
        logger.info(f"Initializing AI monitor loop for camera {self.camera_id}")
        self.start_time = time.time()
        runner = InferenceRunner()
        
        import gc
        
        # Wait for the first frame from the capture thread
        while self.is_running and self.latest_frame is None:
            time.sleep(0.1)
        
        # Process frames continuously
        while self.is_running:
            try:
                frame = self.latest_frame
                if frame is None or getattr(frame, "size", 0) == 0:
                    time.sleep(0.1)
                    continue
                
                self.frames_processed += 1
                
                if self.frames_processed % 50 == 0:
                    gc.collect()
                
                # Run AI inference
                result = runner.run_inference(frame, camera_id=self.camera_id)
                
                # Task 3: Aggressive CUDA Cache Flushing (balanced for FPS)
                if self.frames_processed % 15 == 0 or result.get('classification') == 'theft':
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        
                result['timestamp'] = timezone.now().isoformat()
                result['fps'] = self.get_stats()['fps']
                # Attach native frame dimensions so the frontend can scale bboxes
                result['camera_id'] = self.camera_id
                result['frame_width'] = frame.shape[1]
                result['frame_height'] = frame.shape[0]

                # ── COOLDOWN GATEKEEPER ──────────────────────────────────────
                is_theft_detected = result.get('classification') == 'theft'
                current_time = time.time()
                
                if is_theft_detected and (current_time - self.last_alert_time) >= 5.0:
                    self.last_alert_time = current_time
                    # Proceed: Save DB Alert, Trigger VideoWriter, set is_suspicious=True
                else:
                    # COOLDOWN ACTIVE (or normal frame)
                    # Force normal state for the JSON payload so no alert is created
                    is_theft_detected = False
                    result['classification'] = 'normal'
                    if 'alert_triggered' in result:
                        result['alert_triggered'] = False
                    
                    # We NO LONGER clear `suspicious_tracks` or `is_suspicious` here,
                    # so the frontend Node Graph and camera overlays still receive them
                    # and draw the bounding boxes consistently via Cross-Camera Broadcast.

                self.last_result = result

                # ── CALLBACK FIRST ────────────────────────────────────────────
                # Fire the SSE/WebSocket callback immediately after inference so
                # the frontend canvas receives bounding-box data without waiting
                # for the (slower) database write to complete.
                # Throttled to _SSE_MAX_FPS to keep cloud bandwidth low.
                if self.callback:
                    now = time.time()
                    min_interval = 1.0 / self._SSE_MAX_FPS
                    if (now - self._last_callback_time) >= min_interval:
                        self._last_callback_time = now
                        try:
                            self.callback(self.camera_id, result)
                        except Exception as cb_err:
                            logger.error("Callback raised an error: %s", cb_err)

                # ── DB WRITE (after callback — latency non-critical) ──────────
                # Save to database every 2 seconds (or immediately on theft)
                current_fps = max(1, int(self.get_stats()['fps']))
                should_save = (
                    self.frames_processed % (current_fps * 2) == 0 or  # Every ~2 seconds
                    result['classification'] == 'theft'
                )
                
                if should_save:
                    self._save_result(result)
                
                # Persist tracking records (service handles its own throttle)
                if result.get('tracks'):
                    self._save_tracking_data(result)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                time.sleep(0.5)
        
        logger.info(f"Monitoring loop ended for camera {self.camera_id}")
    
    def _prepare_url(self, rtsp_url: str) -> str:
        """Convert camera URL to stream URL"""
        # If it's an HTTP URL (IP Webcam) without a specific endpoint, add /video
        if rtsp_url.startswith('http://'):
            if rtsp_url.split('/')[-1].startswith(':') or \
               (rtsp_url.count('/') == 2 and (':8080' in rtsp_url or ':4747' in rtsp_url)):
                return rtsp_url.rstrip('/') + '/video'
        return rtsp_url
    
    def _save_result(self, result: Dict):
        """Save inference result to database"""
        try:
            from ..models import AIInference
            from apps.cameras.models import Camera
            from apps.alerts.models import Alert
            
            camera = Camera.objects.get(pk=self.camera_id)
            
            # Create alert if theft detected
            alert = None
            if result['classification'] == 'theft':
                alert = self._create_alert(camera, result)
            
            # Save inference
            AIInference.objects.create(
                camera_id=camera,
                detections=result.get('detections', []),
                poses=result.get('poses', []),
                tracks=result.get('tracks', []),
                classification=result['classification'],
                confidence=result['confidence'],
                frame_metadata=result.get('frame_metadata', {}),
                processing_time_ms=result.get('processing_time_ms', 0),
                alert=alert,
            )
            
            logger.info(f"💾 Saved result for camera {self.camera_id}: {result['classification']} ({result['confidence']:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to save result: {str(e)}")
    
    def _create_alert(self, camera, result):
        """Create alert for theft detection"""
        try:
            from apps.alerts.models import Alert
            
            metadata = {
                'confidence': result['confidence'],
                'suspicious_tracks': result.get('suspicious_tracks', []),
                'num_detections': result['frame_metadata'].get('num_detections', 0),
                'num_persons': result['frame_metadata'].get('num_persons', 0),
                'detected_by': 'CONTINUOUS_MONITOR',
                'detection_timestamp': timezone.now().isoformat(),
                'fps': self.get_stats()['fps'],
            }
            
            alert = Alert.objects.create(
                camera_id=camera,
                alert_type='THEFT_DETECTED',
                severity='HIGH' if result['confidence'] > 0.7 else 'MEDIUM',
                status='ACTIVE',
                metadata=metadata,
            )
            
            logger.warning(f"🚨 THEFT ALERT created for camera {camera.name}: {alert.id}")
            self._try_upload_alert_clip(alert)
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}")
            return None
    
    def _save_tracking_data(self, result: Dict):
        """Persist confirmed tracks to the tracking_records collection."""
        try:
            from apps.tracking.services import TrackingService
            TrackingService.save_tracks(
                camera_id=self.camera_id,
                tracks=result.get('tracks', []),
                inference_result=result,
            )
        except Exception as e:
            logger.error(f"Failed to save tracking data: {str(e)}")
    
    def _try_upload_alert_clip(self, alert) -> None:
        """
        Snapshot the rolling frame buffer and upload a 5-second clip to Cloudinary
        in a background thread so the monitoring loop is not blocked.
        """
        frames = list(self._frame_buffer)  # snapshot — thread-safe copy
        if not frames:
            logger.warning("Frame buffer empty — no clip to upload for alert %s", alert.id)
            return

        alert_id = str(alert.id)

        def _upload_worker(alert_id, frames):
            from .clip_encoding import write_frames_to_mp4
            from apps.alerts.cloudinary_video import upload_video_to_cloudinary
            import django
            django.setup.__module__  # ensure ORM is ready in this thread

            if not frames:
                return

            stats = self.get_stats()
            # Use capture_fps for encoding to ensure real-time playback speed
            fps = float(stats.get("capture_fps") or stats.get("fps") or 0)
            if fps < 5.0:
                fps = 25.0  # safe fallback when FPS not yet settled

            # Take up to 5 seconds worth of frames from the tail of the buffer
            clip_count = min(len(frames), int(fps * 5))
            clip_count = max(clip_count, 8)   # never fewer than 8 frames
            clip_frames = frames[-clip_count:]

            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                import gc
                gc.collect()  # Flush RAM before OpenCV VideoWriter starts allocating

                logger.info("🎬 Encoding %d-frame clip (%.1f s) for alert %s",
                            len(clip_frames), len(clip_frames) / fps, alert_id)
                if not write_frames_to_mp4(clip_frames, tmp_path, fps=fps):
                    logger.error("Clip encoding failed for alert %s", alert_id)
                    return

                # Task 2: Explicitly release the duplicated list references and flush RAM
                del clip_frames
                del frames
                gc.collect()  # Flush RAM after OpenCV VideoWriter explicitly releases

                logger.info("☁️  Uploading clip to Cloudinary for alert %s …", alert_id)
                video_url, public_id = upload_video_to_cloudinary(tmp_path)

                if video_url:
                    # Re-fetch the alert inside this thread to avoid stale state
                    from apps.alerts.models import Alert as AlertModel
                    try:
                        fresh = AlertModel.objects.get(pk=alert_id)
                        fresh.video_url = video_url
                        fresh.video_public_id = public_id
                        fresh.save(update_fields=["video_url", "video_public_id"])
                        logger.info("✅ Clip saved for alert %s → %s", alert_id, video_url)
                    except AlertModel.DoesNotExist:
                        logger.warning("Alert %s no longer exists; discarding clip", alert_id)
                else:
                    logger.warning("Cloudinary returned no URL for alert %s", alert_id)

            except Exception as exc:
                logger.error("Alert clip upload failed for %s: %s", alert_id, exc, exc_info=True)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        t = threading.Thread(target=_upload_worker, args=(alert_id, frames), daemon=True,
                             name=f"clip-upload-{alert_id}")
        t.start()



class MonitorManager:
    """
    Manages multiple continuous monitors
    Singleton service that runs in background
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.monitors: Dict[str, ContinuousMonitor] = {}
        self._initialized = True
        logger.info("📹 MonitorManager initialized")
    
    def start_monitor(self, camera_id: str, rtsp_url: str, callback=None) -> bool:
        """Start monitoring a camera.

        The SSERegistry is always wired as the primary callback so that any
        connected SSE client receives real-time tracking data automatically.
        An optional secondary *callback* argument is still supported for
        callers that need additional custom behaviour.
        """
        if camera_id in self.monitors:
            logger.warning(f"Monitor already exists for camera {camera_id}")
            return False

        from .sse_registry import sse_registry

        def _combined_callback(cam_id: str, result: dict) -> None:
            # Always publish to SSE clients (no-op when no clients connected)
            sse_registry.publish(cam_id, result)
            # Also invoke any caller-supplied secondary callback
            if callback:
                callback(cam_id, result)

        monitor = ContinuousMonitor(camera_id, rtsp_url, _combined_callback)
        if monitor.start():
            self.monitors[camera_id] = monitor
            return True
        return False
    
    def stop_monitor(self, camera_id: str) -> bool:
        """Stop monitoring a camera"""
        if camera_id not in self.monitors:
            logger.warning(f"No monitor found for camera {camera_id}")
            return False
        
        monitor = self.monitors[camera_id]
        monitor.stop()
        del self.monitors[camera_id]
        return True
    
    def get_monitor_stats(self, camera_id: str) -> Optional[Dict]:
        """Get stats for a specific monitor"""
        if camera_id in self.monitors:
            return self.monitors[camera_id].get_stats()
        return None
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get stats for all monitors"""
        return {
            camera_id: monitor.get_stats()
            for camera_id, monitor in self.monitors.items()
        }
    
    def stop_all(self):
        """Stop all monitors"""
        for camera_id in list(self.monitors.keys()):
            self.stop_monitor(camera_id)


# Global instance
monitor_manager = MonitorManager()

