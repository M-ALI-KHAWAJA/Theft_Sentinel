# 🔧 Camera RTSP Troubleshooting Guide

## 🚨 Error: "Failed to capture frame from camera" (500 Error)

This error occurs when the backend cannot capture frames from your camera's RTSP stream.

---

## 🔍 Quick Diagnosis

### Step 1: Run the Test Script

```bash
python test_camera_rtsp.py
```

This will test all cameras and show you exactly what's wrong.

**Expected output for working camera:**
```
Testing Camera: Ali Mobile
✓ Stream opened successfully
✓ Frame captured successfully
  - Frame shape: (720, 1280, 3)
✅ Camera is working correctly!
```

**Expected output for broken camera:**
```
Testing Camera: Mohid Mobile
❌ FAILED: Could not open RTSP stream

Possible issues:
  1. Camera is offline
  2. RTSP URL is incorrect
  3. Wrong credentials
  ...
```

---

## 🛠️ Common Issues & Solutions

### Issue 1: Invalid RTSP URL

**Symptoms:**
- "Failed to open RTSP stream"
- "Could not connect to camera"

**Solution:**

Check your camera's RTSP URL format:

```python
# Django shell
python manage.py shell

>>> from apps.cameras.models import Camera
>>> camera = Camera.objects.get(name='Ali Mobile')
>>> print(camera.rtsp_url)
```

**Valid RTSP URL formats:**

```bash
# IP Camera (with auth)
rtsp://username:password@192.168.1.100:554/stream1

# IP Camera (no auth)
rtsp://192.168.1.100:554/stream1

# Mobile phone as camera (using IP Webcam app)
http://192.168.1.50:8080/video

# DroidCam
http://192.168.1.50:4747/video
```

**Update camera URL:**

```python
>>> camera.rtsp_url = 'rtsp://admin:password@192.168.1.100:554/stream1'
>>> camera.save()
```

---

### Issue 2: Camera Offline/Unreachable

**Symptoms:**
- Connection timeout
- "Could not open RTSP stream"

**Diagnosis:**

```bash
# Test network connectivity
ping 192.168.1.100

# Test if RTSP port is open (usually 554)
telnet 192.168.1.100 554
# or
nc -zv 192.168.1.100 554
```

**Solutions:**
1. ✅ Ensure camera is powered on
2. ✅ Check camera is on same network
3. ✅ Verify firewall isn't blocking RTSP port
4. ✅ Check camera's IP address hasn't changed

---

### Issue 3: Wrong Credentials

**Symptoms:**
- "Authentication failed"
- "401 Unauthorized"

**Solution:**

Update credentials in RTSP URL:

```python
python manage.py shell

>>> from apps.cameras.models import Camera
>>> camera = Camera.objects.get(name='Ali Mobile')
>>> camera.rtsp_url = 'rtsp://NEW_USER:NEW_PASSWORD@ip:port/stream'
>>> camera.save()
```

---

### Issue 4: Using Mobile Phone as Camera

**If using IP Webcam (Android):**

1. Install "IP Webcam" from Play Store
2. Open app → Start Server
3. Note the URL (e.g., `http://192.168.1.50:8080`)
4. Update camera URL:

```python
>>> camera.rtsp_url = 'http://192.168.1.50:8080/video'
>>> camera.save()
```

**If using DroidCam:**

```python
>>> camera.rtsp_url = 'http://192.168.1.50:4747/video'
>>> camera.save()
```

---

### Issue 5: OpenCV Not Installed Properly

**Symptoms:**
- "No module named 'cv2'"
- "OpenCV not found"

**Solution:**

```bash
# Reinstall OpenCV
pip uninstall opencv-python opencv-python-headless
pip install opencv-python
```

**Test OpenCV:**

```python
import cv2
print(cv2.__version__)  # Should show version like 4.8.0
```

---

### Issue 6: Network/Firewall Blocking

**Symptoms:**
- Intermittent failures
- Timeout errors

**Solutions:**

**For Windows:**
```powershell
# Allow Python through firewall
netsh advfirewall firewall add rule name="Python" dir=in action=allow program="C:\Python39\python.exe"
```

**For Linux:**
```bash
# Allow RTSP port
sudo ufw allow 554/tcp
```

---

## 📋 Camera Configuration Checklist

### ✅ For IP Cameras:

- [ ] Camera is powered on
- [ ] Camera is connected to network
- [ ] RTSP is enabled in camera settings
- [ ] Username and password are correct
- [ ] RTSP port is accessible (default: 554)
- [ ] Firewall allows RTSP traffic

### ✅ For Mobile Phone Cameras:

- [ ] App (IP Webcam/DroidCam) is installed
- [ ] App server is started
- [ ] Phone is on same WiFi network
- [ ] Phone's IP address is noted
- [ ] URL format is correct (http, not rtsp)

### ✅ For Django Backend:

- [ ] OpenCV is installed (`pip show opencv-python`)
- [ ] Camera model exists in database
- [ ] RTSP URL is correctly saved
- [ ] Backend can access camera network
- [ ] No firewall blocking outgoing connections

---

## 🧪 Testing Different Camera Types

### Test IP Camera (RTSP)

```bash
# Using VLC (install VLC first)
vlc rtsp://username:password@192.168.1.100:554/stream1

# Using ffplay (part of ffmpeg)
ffplay rtsp://username:password@192.168.1.100:554/stream1

# Using OpenCV
python -c "import cv2; cap = cv2.VideoCapture('rtsp://user:pass@ip:port/stream'); print(cap.isOpened())"
```

### Test Mobile Camera (HTTP)

```bash
# Using browser
http://192.168.1.50:8080

# Using curl
curl -I http://192.168.1.50:8080/video

# Using VLC
vlc http://192.168.1.50:8080/video
```

---

## 🔧 Fix Camera URLs in Database

### View all cameras:

```bash
python manage.py shell
```

```python
from apps.cameras.models import Camera

# List all cameras
for camera in Camera.objects.all():
    print(f"{camera.name}: {camera.rtsp_url}")
```

### Update camera URL:

```python
# Get specific camera
camera = Camera.objects.get(name='Ali Mobile')

# Update RTSP URL
camera.rtsp_url = 'rtsp://admin:password@192.168.1.100:554/stream1'
camera.status = 'ONLINE'
camera.save()

print("✓ Camera updated")
```

### Bulk update for IP Webcam:

```python
# If all cameras are mobile phones using IP Webcam
Camera.objects.filter(name__contains='Mobile').update(
    rtsp_url='http://192.168.1.50:8080/video'
)
```

---

## 🔍 Debug Mode (Detailed Logs)

Enable detailed logging to see exact errors:

### 1. Update settings.py:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.ai_engine': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Changed from INFO
            'propagate': False,
        },
    },
}
```

### 2. Restart server and check logs:

```bash
python manage.py runserver
```

Look for lines like:
```
INFO - Attempting to capture from RTSP: rtsp://admin:***@192...
ERROR - Failed to open RTSP stream: rtsp://...
ERROR - Possible reasons: Invalid URL, camera offline...
```

---

## 🚀 Quick Fixes

### Fix 1: Reset Camera to Test Mode

```python
python manage.py shell

from apps.cameras.models import Camera

# Use a test video file instead of RTSP
camera = Camera.objects.get(name='Ali Mobile')
camera.rtsp_url = '/path/to/test_video.mp4'  # Use a local video file
camera.save()
```

### Fix 2: Use Fake Camera for Testing

```python
# Create a test camera that always works
Camera.objects.create(
    name='Test Camera',
    rtsp_url='0',  # Use webcam
    location='Test',
    zone='Test',
    status='ONLINE'
)
```

### Fix 3: Skip Camera Capture (Test AI Only)

For testing the AI without camera:

```bash
# Use analyze-frame endpoint instead
POST /api/ai/analyze-frame/
Body: {
  "frame": "<base64_image>",
  "save_to_db": false
}
```

---

## 📞 Still Not Working?

### 1. Collect Debug Info:

```bash
python test_camera_rtsp.py > camera_debug.txt 2>&1
```

### 2. Check Django Logs:

```bash
# Look for errors in terminal where Django is running
```

### 3. Test OpenCV Directly:

```python
import cv2
cap = cv2.VideoCapture('YOUR_RTSP_URL')
print(f"Opened: {cap.isOpened()}")
ret, frame = cap.read()
print(f"Frame captured: {ret}")
if frame is not None:
    print(f"Frame shape: {frame.shape}")
    cv2.imwrite('test_frame.jpg', frame)
    print("✓ Frame saved as test_frame.jpg")
cap.release()
```

### 4. Common Camera RTSP URLs:

**Hikvision:**
```
rtsp://admin:password@ip:554/Streaming/Channels/101
```

**Dahua:**
```
rtsp://admin:password@ip:554/cam/realmonitor?channel=1&subtype=0
```

**Axis:**
```
rtsp://root:password@ip/axis-media/media.amp
```

**TP-Link:**
```
rtsp://admin:password@ip:554/stream1
```

**Mobile (IP Webcam):**
```
http://ip:8080/video
```

---

## ✅ Verification Steps

After fixing, verify it works:

```bash
# 1. Test with script
python test_camera_rtsp.py

# 2. Test API endpoint
curl -X POST http://localhost:8000/api/ai/process-camera/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"camera_id": "YOUR_CAMERA_ID"}'

# 3. Test in frontend
# Click "Start" button in AI Monitor page
```

---

## 🎉 Success!

If all tests pass, your cameras should work with the AI monitoring system!

