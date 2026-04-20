# Camera Feed Setup Guide

## Issue Fixed
1. ✅ Changed URL patterns from `<int:pk>` to `<str:pk>` for MongoDB ObjectId compatibility
2. ✅ Added camera feed streaming endpoint
3. ✅ Installed opencv-python for video processing

## Changes Made

### 1. Updated URLs (`apps/cameras/urls.py`)
- Changed all `<int:pk>` to `<str:pk>` to support MongoDB ObjectId
- Added new endpoint: `/api/cameras/<camera_id>/feed/` for live streaming

### 2. Added Camera Feed View (`apps/cameras/views.py`)
- New `CameraFeedView` class that streams RTSP feeds
- Converts RTSP stream to MJPEG format for browser compatibility
- Includes retry logic and error handling

### 3. Installed Dependencies
```bash
pip install opencv-python
```

## How to Use

### Backend Endpoints

#### 1. Get Camera List
```bash
GET /api/cameras/
```

#### 2. Create Camera
```bash
POST /api/cameras/
{
  "name": "Main Entrance Camera",
  "rtsp_url": "rtsp://192.168.1.100:554/stream",
  "location": "Building A - Floor 1",
  "zone": "Zone A",
  "status": "ONLINE"
}
```

#### 3. Get Live Feed
```bash
GET /api/cameras/<camera_id>/feed/
```

### Frontend Integration

#### Option 1: Using img tag (Recommended)
```jsx
<img 
  src={`http://localhost:8000/api/cameras/${cameraId}/feed/`}
  alt="Live Camera Feed"
  style={{ width: '100%', height: 'auto' }}
/>
```

#### Option 2: Using video tag with RTSP (Requires browser plugin)
```jsx
<video 
  src={camera.rtsp_url}
  controls
  autoPlay
  style={{ width: '100%', height: 'auto' }}
/>
```

#### Option 3: Using HLS/DASH (Requires conversion)
For production, consider using a media server like:
- **nginx-rtmp-module**: Convert RTSP to HLS
- **FFmpeg**: Convert RTSP to HLS/DASH
- **WebRTC**: For low-latency streaming

## Restart Server

**IMPORTANT**: You need to restart the Django server for changes to take effect:

1. Stop the current server (Ctrl+C in terminal 2)
2. Restart with:
```bash
cd /d/ALi/fyp_backend/theft_sentinel_backend
source ../env/Scripts/activate
python manage.py runserver
```

## Testing

### Test Camera Feed
```bash
# Create a test camera
curl -X POST http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "rtsp_url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
    "location": "Test Location",
    "zone": "Test Zone",
    "status": "ONLINE"
  }'

# Access feed in browser
http://localhost:8000/api/cameras/<camera_id>/feed/
```

## Troubleshooting

### 1. "Module 'cv2' not found"
```bash
cd /d/ALi/fyp_backend
source env/Scripts/activate
pip install opencv-python
```

### 2. "Camera is offline"
- Check camera status in database
- Update status to "ONLINE":
```bash
PATCH /api/cameras/<camera_id>/status/
{
  "status": "ONLINE"
}
```

### 3. "Failed to connect to camera stream"
- Verify RTSP URL is correct
- Check network connectivity to camera
- Ensure camera supports RTSP protocol
- Test RTSP URL with VLC media player first

### 4. High latency or buffering
- Reduce frame quality in `CameraFeedView` (change JPEG quality from 85 to 70)
- Increase buffer size
- Use WebRTC for lower latency

## Production Recommendations

For production deployment:

1. **Use a Media Server**:
   - nginx-rtmp-module
   - Wowza Streaming Engine
   - Red5 Pro

2. **Convert to HLS/DASH**:
   - Better browser compatibility
   - Adaptive bitrate streaming
   - CDN support

3. **Implement Caching**:
   - Cache frames to reduce CPU usage
   - Use Redis for frame storage

4. **Load Balancing**:
   - Distribute camera streams across multiple servers
   - Use WebSocket for real-time updates

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cameras/` | GET | List all cameras |
| `/api/cameras/` | POST | Create new camera |
| `/api/cameras/<id>/` | GET | Get camera details |
| `/api/cameras/<id>/` | PUT/PATCH | Update camera |
| `/api/cameras/<id>/` | DELETE | Delete camera |
| `/api/cameras/<id>/status/` | PATCH | Update camera status |
| `/api/cameras/<id>/feed/` | GET | **Live camera feed** |
| `/api/cameras/zone/<zone>/` | GET | Get cameras by zone |

---

**Status**: ✅ Ready to use (after server restart)
**Date**: November 24, 2025

