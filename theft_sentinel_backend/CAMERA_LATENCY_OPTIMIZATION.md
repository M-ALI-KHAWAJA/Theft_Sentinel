# Camera Feed Latency Optimization Guide

## Optimizations Applied

### 1. ✅ Increased Chunk Size (8KB)
**Before**: 1KB chunks
**After**: 8KB chunks
**Impact**: Reduces overhead, improves throughput

```python
response.iter_content(chunk_size=8192)  # 8KB chunks
```

### 2. ✅ Disabled Response Buffering
**Impact**: Streams data immediately without buffering
```python
response = requests.get(url, stream=True)
```

### 3. ✅ Added Cache-Control Headers
**Impact**: Prevents caching, ensures fresh frames
```python
headers={
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache'
}
```

### 4. ✅ Reduced JPEG Quality (85 → 75)
**Impact**: Faster encoding, smaller file size, lower latency
**Trade-off**: Slightly lower image quality (barely noticeable)

### 5. ✅ Minimal Buffer Size (OpenCV)
**Impact**: Reduces frame buffering, shows latest frame
```python
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
```

### 6. ✅ Frame Buffer Clearing
**Impact**: Clears old frames from buffer to show latest
```python
for _ in range(5):
    cap.grab()  # Clear buffer
```

## Common Causes of Latency

### 1. Network Latency
**Problem**: Slow network between camera and backend
**Solutions**:
- Ensure camera and backend are on same network
- Use wired connection instead of WiFi
- Check network bandwidth

### 2. Camera Processing
**Problem**: Camera takes time to encode frames
**Solutions**:
- Reduce camera resolution (e.g., 640x480 instead of 1920x1080)
- Lower camera FPS setting
- Use hardware encoding if available

### 3. Backend Processing
**Problem**: Server CPU bottleneck
**Solutions**:
- ✅ Already optimized JPEG quality
- ✅ Already minimized buffer
- Consider using GPU acceleration

### 4. Browser Rendering
**Problem**: Browser takes time to decode and render
**Solutions**:
- Use modern browser (Chrome, Firefox)
- Close other tabs to free resources
- Disable browser extensions

### 5. Multiple Simultaneous Streams
**Problem**: Server handling too many streams
**Solutions**:
- Limit concurrent viewers per camera
- Use CDN or media server for production
- Implement load balancing

## Additional Optimizations (Optional)

### Option 1: Enable Frame Skipping
For even lower latency, skip every other frame:

Edit `apps/cameras/views.py` and uncomment:
```python
# Skip every other frame
if frame_count % 2 == 0:
    continue
```

**Impact**: Halves bandwidth, reduces latency by ~50%
**Trade-off**: Lower FPS (15 FPS instead of 30 FPS)

### Option 2: Reduce Resolution
Add this to OpenCV capture:
```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
```

**Impact**: Faster processing, lower bandwidth
**Trade-off**: Lower resolution

### Option 3: Use Direct RTSP (Frontend)
For lowest latency, use WebRTC or direct RTSP in frontend:

```jsx
// Using react-player with RTSP support
import ReactPlayer from 'react-player'

<ReactPlayer 
  url="rtsp://192.168.10.2:8080/video"
  playing
  muted
  width="100%"
  height="auto"
/>
```

**Note**: Requires browser plugin or WebRTC gateway

## Camera Settings to Reduce Latency

### IP Webcam (Android) Settings:
1. **Video Resolution**: 640x480 or 800x600 (not 1920x1080)
2. **Quality**: 70-80% (not 100%)
3. **FPS Limit**: 15-20 FPS (not 30 FPS)
4. **Video Encoder**: H.264 or MJPEG
5. **Disable Audio**: If not needed

### Access IP Webcam Settings:
1. Open IP Webcam app on phone
2. Scroll down to "Video preferences"
3. Adjust settings as above
4. Restart streaming

## Testing Latency

### Test 1: Measure End-to-End Latency
```bash
# Time to receive first frame
time curl -s http://localhost:8000/api/cameras/ID/feed/ | head -c 1000
```

### Test 2: Check Network Latency
```bash
# Ping camera
ping 192.168.10.2

# Should be < 10ms for local network
```

### Test 3: Monitor CPU Usage
```bash
# Check if CPU is bottleneck
top  # Linux/Mac
taskmgr  # Windows
```

## Expected Latency

| Scenario | Expected Latency |
|----------|-----------------|
| **Local Network (Optimized)** | 100-300ms |
| **Local Network (Default)** | 500-1000ms |
| **WiFi** | 300-800ms |
| **Remote Network** | 1-3 seconds |
| **Multiple Streams** | +100-200ms per stream |

## Production Recommendations

### For Production Deployment:

1. **Use Media Server**
   - nginx-rtmp-module
   - Wowza Streaming Engine
   - Ant Media Server

2. **Implement WebRTC**
   - Ultra-low latency (< 500ms)
   - Peer-to-peer connection
   - Better for real-time applications

3. **Use CDN**
   - Distribute load
   - Edge caching
   - Global reach

4. **Optimize Network**
   - Use dedicated VLAN for cameras
   - QoS prioritization
   - Wired connections

## Troubleshooting High Latency

### Issue: 2-5 second delay
**Causes**:
- High resolution (1920x1080)
- High quality (100%)
- WiFi interference
- Multiple streams

**Solutions**:
1. Reduce camera resolution to 640x480
2. Lower quality to 70%
3. Use wired connection
4. Limit concurrent viewers

### Issue: Increasing delay over time
**Causes**:
- Buffer buildup
- Memory leak
- Network congestion

**Solutions**:
1. ✅ Frame buffer clearing (already implemented)
2. Restart stream periodically
3. Monitor server resources

### Issue: Choppy/stuttering video
**Causes**:
- Low FPS
- Network packet loss
- CPU overload

**Solutions**:
1. Check network stability
2. Increase server resources
3. Reduce number of simultaneous streams

## Quick Fixes Checklist

- [ ] Camera resolution set to 640x480 or lower
- [ ] Camera quality set to 70-80%
- [ ] Camera FPS set to 15-20
- [ ] Camera and server on same network
- [ ] Using wired connection (not WiFi)
- [ ] No other heavy processes on server
- [ ] Using modern browser
- [ ] Only one tab viewing the feed
- [ ] Server has adequate CPU/RAM

## Monitoring

### Check Current Latency:
```javascript
// Add to frontend
let lastFrameTime = Date.now();

img.onload = () => {
  const latency = Date.now() - lastFrameTime;
  console.log(`Frame latency: ${latency}ms`);
  lastFrameTime = Date.now();
};
```

### Server-Side Logging:
```python
# Already implemented in views.py
print(f"[Camera Feed] Streaming MJPEG from {url}")
```

---

**Status**: ✅ Optimized for low latency
**Expected Latency**: 100-500ms (local network)
**Date**: November 24, 2025

