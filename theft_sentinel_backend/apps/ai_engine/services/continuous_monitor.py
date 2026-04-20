"""
Continuous Camera Monitoring Service
Runs your existing AI pipeline continuously on camera streams
Stores results in database for frontend to read in real-time
"""
import cv2
import os
import sys
import tempfile
import time
import threading
import logging
from collections import deque
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from django.utils import timezone

# Add ModelExport to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_EXPORT_PATH = BASE_DIR / "ModelExport"
sys.path.insert(0, str(MODEL_EXPORT_PATH))

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """
    Runs continuous AI monitoring on camera streams
    Processes frames at full FPS (15-30) instead of 2-second intervals
    """
    
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
        self.cap = None
        
        # Stats
        self.frames_processed = 0
        self.start_time = None
        self.last_result = None
        self.error_count = 0
        
        # Rolling frame buffer (~5s at 30 FPS) for theft clip generation
        self._frame_buffer = deque(maxlen=150)
        
        # Import your pipeline (lazy import)
        self.pipeline = None
    
    def start(self):
        """Start continuous monitoring in background thread"""
        if self.is_running:
            logger.warning(f"Monitor already running for camera {self.camera_id}")
            return False
        
        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"🎥 Started continuous monitoring for camera {self.camera_id}")
        return True
    
    def stop(self):
        """Stop continuous monitoring"""
        self.is_running = False
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
        else:
            fps = 0
            elapsed = 0
        
        return {
            'camera_id': self.camera_id,
            'is_running': self.is_running,
            'frames_processed': self.frames_processed,
            'fps': round(fps, 2),
            'elapsed_seconds': round(elapsed, 2),
            'error_count': self.error_count,
            'last_result': self.last_result,
        }
    
    def _monitor_loop(self):
        """Main monitoring loop - runs continuously"""
        from .inference_runner import InferenceRunner
        from ..utils.frame_utils import capture_frame_from_rtsp
        
        logger.info(f"Initializing continuous monitoring for {self.rtsp_url}")
        self.start_time = time.time()
        runner = InferenceRunner()
        
        # Open video stream
        processed_url = self._prepare_url(self.rtsp_url)
        self.cap = cv2.VideoCapture(processed_url)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open stream: {processed_url}")
            self.is_running = False
            return
        
        logger.info(f"✅ Stream opened successfully for camera {self.camera_id}")
        
        # Process frames continuously
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
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
                
                # Reset error count on success
                self.error_count = 0
                self.frames_processed += 1
                self._frame_buffer.append(frame.copy())
                
                # Run AI inference
                result = runner.process_frame(frame, camera_id=self.camera_id)
                result['timestamp'] = timezone.now().isoformat()
                result['fps'] = self.get_stats()['fps']
                
                self.last_result = result
                
                # Save to database every 2 seconds (or on theft detection)
                should_save = (
                    self.frames_processed % 60 == 0 or  # Every ~2 seconds at 30 FPS
                    result['classification'] == 'theft'
                )
                
                if should_save:
                    self._save_result(result)
                
                # Call callback if provided (for WebSocket updates)
                if self.callback:
                    self.callback(self.camera_id, result)
                
                # Optionally limit FPS (remove to run at full speed)
                # time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)
                self.error_count += 1
                time.sleep(0.5)
        
        # Cleanup
        if self.cap:
            self.cap.release()
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
    
    def _try_upload_alert_clip(self, alert) -> None:
        """Encode last few seconds from the rolling buffer, upload to Cloudinary, save URL."""
        from .clip_encoding import write_frames_to_mp4
        from apps.alerts.cloudinary_video import upload_video_to_cloudinary
        
        frames = list(self._frame_buffer)
        if not frames:
            return
        
        stats = self.get_stats()
        fps = float(stats.get("fps") or 0)
        if fps < 5.0:
            fps = 25.0
        
        min_clip = max(8, int(fps * 3))
        max_clip = min(len(frames), int(fps * 5))
        preferred = int(fps * 4)
        clip_count = min(len(frames), max(min_clip, min(max_clip, preferred)))
        clip_frames = frames[-clip_count:]
        
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            if not write_frames_to_mp4(clip_frames, tmp_path, fps=fps):
                return
            video_url, public_id = upload_video_to_cloudinary(tmp_path)
            if video_url:
                alert.video_url = video_url
                alert.video_public_id = public_id
                alert.save(update_fields=["video_url", "video_public_id"])
        except Exception as e:
            logger.error(f"Alert clip upload failed: {e}", exc_info=True)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


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
        """Start monitoring a camera"""
        if camera_id in self.monitors:
            logger.warning(f"Monitor already exists for camera {camera_id}")
            return False
        
        monitor = ContinuousMonitor(camera_id, rtsp_url, callback)
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

