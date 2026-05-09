"""
Frame Utilities
Handle frame decoding, encoding, and preprocessing
"""
import cv2
import base64
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def decode_base64_frame(base64_string: str) -> Optional[np.ndarray]:
    """
    Decode base64 string to OpenCV frame
    """
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        
        # Decode image
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            logger.error("Failed to decode frame from base64")
            return None
        
        return frame
        
    except Exception as e:
        logger.error(f"Error decoding base64 frame: {str(e)}")
        return None


def encode_frame_to_base64(frame: np.ndarray, format: str = '.jpg', quality: int = 90) -> Optional[str]:
    """
    Encode OpenCV frame to base64 string
    """
    try:
        if format == '.jpg':
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        else:
            encode_param = []
        
        _, buffer = cv2.imencode(format, frame, encode_param)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        return jpg_as_text
        
    except Exception as e:
        logger.error(f"Error encoding frame to base64: {str(e)}")
        return None


def capture_frame_from_rtsp(rtsp_url: str, timeout: int = 5) -> Optional[np.ndarray]:
    """
    Capture a single frame from RTSP stream or IP Webcam
    For IP Webcam: Database has base URL, but we need /video endpoint for streaming
    """
    cap = None
    try:
        # Convert IP Webcam base URL to video stream URL
        processed_url = rtsp_url
        
        # If it's an HTTP URL (IP Webcam) without a specific endpoint, add /video
        if rtsp_url.startswith('http://'):
            # Check if URL ends with port only (like :8080 or :4747)
            if rtsp_url.split('/')[-1].startswith(':') or \
               (rtsp_url.count('/') == 2 and (':8080' in rtsp_url or ':4747' in rtsp_url)):
                # It's a base URL like http://192.168.10.33:8080
                # Need to add /video for the actual stream
                processed_url = rtsp_url.rstrip('/') + '/video'
                logger.info(f"Converted IP Webcam URL: {rtsp_url} -> {processed_url}")
        
        logger.info(f"Attempting to capture from: {processed_url[:50]}...")

        # TASK 1: Explicit CAP_FFMPEG so OPENCV_FFMPEG_CAPTURE_OPTIONS (UDP transport)
        # is honoured. Without this, Windows auto-selection probes MSMF first, which
        # sends a TCP RTSP SETUP to MediaMTX before FFmpeg sees the env-var.
        cap = cv2.VideoCapture(processed_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency

        # Set timeout
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)

        # TASK 4: Log which backend was selected and warn if not FFMPEG
        backend = cap.getBackendName()
        if backend != "FFMPEG":
            logger.warning(
                f"⚠️ Non-FFmpeg backend detected in capture_frame_from_rtsp: "
                f"{backend} — transport may default to TCP"
            )
        else:
            logger.debug(f"📡 capture_frame_from_rtsp backend=FFMPEG (UDP): {processed_url[:50]}...")
        
        if not cap.isOpened():
            logger.error(f"Failed to open stream: {processed_url}")
            logger.error("Possible reasons: Invalid URL, camera offline, network issue, or wrong credentials")
            return None
        
        # Try to read frame
        ret, frame = cap.read()
        
        if not ret:
            logger.error(f"Failed to read frame from stream: {processed_url}")
            logger.error("Camera may be streaming but no frame received. Check stream format.")
            return None
            
        if frame is None:
            logger.error(f"Frame is None from stream: {processed_url}")
            return None
        
        logger.info(f"✅ Successfully captured frame: {frame.shape}")
        return frame
        
    except Exception as e:
        logger.error(f"Exception capturing frame: {str(e)}", exc_info=True)
        return None
        
    finally:
        if cap is not None:
            cap.release()


def resize_frame(frame: np.ndarray, max_width: int = 1280, max_height: int = 720) -> np.ndarray:
    """
    Resize frame while maintaining aspect ratio
    """
    h, w = frame.shape[:2]
    
    if w <= max_width and h <= max_height:
        return frame
    
    # Calculate scaling factor
    scale = min(max_width / w, max_height / h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return resized


def validate_frame(frame: np.ndarray) -> Tuple[bool, Optional[str]]:
    """
    Validate frame is suitable for processing
    """
    if frame is None:
        return False, "Frame is None"
    
    if not isinstance(frame, np.ndarray):
        return False, "Frame is not a numpy array"
    
    if len(frame.shape) != 3:
        return False, "Frame must be a 3D array (H, W, C)"
    
    h, w, c = frame.shape
    
    if c != 3:
        return False, "Frame must have 3 channels (BGR)"
    
    if h < 100 or w < 100:
        return False, "Frame is too small (min 100x100)"
    
    if h > 4096 or w > 4096:
        return False, "Frame is too large (max 4096x4096)"
    
    return True, None


def draw_detections_on_frame(
    frame: np.ndarray,
    detections: list,
    tracks: list,
    poses: list
) -> np.ndarray:
    """
    Draw detection results on frame for visualization
    """
    vis_frame = frame.copy()
    
    # Draw tracks with bboxes
    for track in tracks:
        bbox = track['bbox']
        x1, y1, x2, y2 = map(int, bbox)
        
        # Color based on ML score
        ml_score = track.get('ml_score', 0.0)
        if ml_score > 0.7:
            color = (0, 0, 255)  # Red for suspicious
        elif ml_score > 0.4:
            color = (0, 165, 255)  # Orange for medium
        else:
            color = (0, 255, 0)  # Green for normal
        
        # Draw bbox
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"Track {track['track_id']} - {track['class']}"
        if ml_score > 0.3:
            label += f" [{int(ml_score*100)}%]"
        
        cv2.putText(vis_frame, label, (x1, max(15, y1 - 8)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Draw pose keypoints
    skeleton_pairs = [
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
        (11, 12), (5, 11), (6, 12), (11, 13), (13, 15),
        (12, 14), (14, 16), (0, 5), (0, 6),
    ]
    
    for pose in poses:
        kps = np.array(pose['keypoints'])
        
        # Draw skeleton
        for (i, j) in skeleton_pairs:
            if i < len(kps) and j < len(kps):
                xi, yi, ci = kps[i]
                xj, yj, cj = kps[j]
                if ci > 0.3 and cj > 0.3:
                    cv2.line(vis_frame,
                            (int(xi), int(yi)),
                            (int(xj), int(yj)),
                            (0, 255, 255), 2)
        
        # Draw wrists
        if len(kps) > 10:
            rwx, rwy, rc = kps[10]
            lwx, lwy, lc = kps[9]
            if rc > 0.3:
                cv2.circle(vis_frame, (int(rwx), int(rwy)), 5, (0, 0, 255), -1)
            if lc > 0.3:
                cv2.circle(vis_frame, (int(lwx), int(lwy)), 5, (0, 255, 0), -1)
    
    return vis_frame

