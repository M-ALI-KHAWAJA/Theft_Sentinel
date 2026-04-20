# AI Engine Quick Start Guide

## ⚡ 5-Minute Setup

### 1. Run Migrations
```bash
python manage.py migrate ai_engine
```

### 2. Start Server
```bash
python manage.py runserver
```

The AI models will load automatically. Look for:
```
✅ Detection model loaded
✅ Pose model loaded
✅ ML classifier loaded
✅ AI Service initialized successfully!
```

### 3. Test It Works
```bash
curl http://localhost:8000/api/ai/health/
```

Expected response:
```json
{"status": "healthy", "models_loaded": true, "device": "cuda:0"}
```

## 🎯 Common Use Cases

### Use Case 1: Analyze a Frame
```python
import requests
import base64
import cv2

# Load image
frame = cv2.imread("frame.jpg")
_, buffer = cv2.imencode('.jpg', frame)
frame_b64 = base64.b64encode(buffer).decode('utf-8')

# Analyze
response = requests.post(
    "http://localhost:8000/api/ai/analyze-frame/",
    headers={"Authorization": f"Bearer {your_token}"},
    json={"frame": frame_b64}
)

result = response.json()
print(f"Classification: {result['classification']}")
print(f"Confidence: {result['confidence']}")
```

### Use Case 2: Monitor Camera Stream
```python
import requests
import time

camera_id = "your_camera_id"

while True:
    response = requests.post(
        "http://localhost:8000/api/ai/process-camera/",
        headers={"Authorization": f"Bearer {your_token}"},
        json={"camera_id": camera_id}
    )
    
    result = response.json()
    
    if result['classification'] == 'theft':
        print(f"🚨 THEFT DETECTED! Confidence: {result['confidence']}")
        # Alert created automatically
    
    time.sleep(1)  # Process every second
```

### Use Case 3: Real-Time Processing with Continuous Tracking
```python
import cv2
import base64
import requests
from apps.ai_engine.services.inference_runner import InferenceRunner

# Initialize runner (maintains tracking state)
runner = InferenceRunner()

cap = cv2.VideoCapture(rtsp_url)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process frame (tracking persists across frames)
    result = runner.process_frame(frame, camera_id="cam_123")
    
    # Check for theft
    if result['classification'] == 'theft':
        print(f"🚨 Theft! Score: {result['confidence']}")
        for track in result['suspicious_tracks']:
            print(f"  Track {track['track_id']}: {track['ml_score']}")
    
    # Visualize
    for track in result['tracks']:
        bbox = track['bbox']
        cv2.rectangle(frame, 
                     (int(bbox[0]), int(bbox[1])),
                     (int(bbox[2]), int(bbox[3])),
                     (0, 255, 0), 2)
    
    cv2.imshow("AI Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## 🔑 Getting JWT Token

```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login/",
    json={
        "username": "your_username",
        "password": "your_password"
    }
)

token = response.json()['access']
print(f"Token: {token}")
```

## 📊 Response Structure

### Detection Object
```json
{
  "bbox": [x1, y1, x2, y2],
  "confidence": 0.85,
  "class": "person",
  "class_id": 0
}
```

### Track Object
```json
{
  "track_id": 1,
  "bbox": [x1, y1, x2, y2],
  "class": "person",
  "confidence": 0.88,
  "dwell_time": 150,
  "ml_score": 0.75
}
```

### Pose Object
```json
{
  "track_id": 1,
  "keypoints": [[x, y, conf], ...],  // 17 keypoints
  "confidence": 0.90,
  "features": {
    "torso_angle": 45.2,
    "left_elbow_angle": 120.5,
    "right_elbow_angle": 115.8,
    "left_wrist_speed": 5.2,
    "right_wrist_speed": 12.5
  }
}
```

### Suspicious Track Object
```json
{
  "track_id": 1,
  "ml_score": 0.87,
  "behavior": {
    "hand_in_bag": 18,
    "hand_in_torso": 12,
    "fast_wrist": 8,
    "near_object": 15,
    "concealment_events": 3
  }
}
```

## 🎨 Keypoint Indices

```python
# COCO 17 keypoint format
KEYPOINTS = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle"
}
```

## ⚙️ Configuration

### Inference Parameters

In `apps/ai_engine/services/inference_runner.py`:

```python
class InferenceRunner:
    def __init__(self):
        # Detection config
        self.det_conf = 0.45      # Detection confidence
        self.det_iou = 0.50       # Detection IoU threshold
        self.det_imgsz = 704      # Detection image size
        
        # Pose config
        self.pose_conf = 0.30     # Pose confidence
        self.pose_iou = 0.50      # Pose IoU threshold
        self.pose_imgsz = 320     # Pose image size
```

### Theft Threshold

In `apps/ai_engine/services/inference_runner.py`, line ~523:

```python
if ml_score > 0.5:  # <-- Adjust this threshold
    theft_detected = True
```

## 🚨 Alert Integration

Alerts are created automatically when theft is detected:

```python
# Alert is created via existing code:
from apps.alerts.serializers import AlertCreateSerializer

alert_data = {
    'camera_id': camera.id,
    'alert_type': 'THEFT_DETECTED',
    'severity': 'HIGH' if confidence > 0.7 else 'MEDIUM',
    'metadata': {
        'confidence': 0.87,
        'suspicious_tracks': [...],
        'detected_by': 'AI_ENGINE'
    }
}

alert_serializer = AlertCreateSerializer(data=alert_data)
alert = alert_serializer.save()
```

## 📝 Database Queries

### Get Recent Theft Detections
```python
from apps.ai_engine.models import AIInference

recent_thefts = AIInference.objects.filter(
    classification='theft',
    confidence__gte=0.7
).order_by('-timestamp')[:10]

for inference in recent_thefts:
    print(f"Camera: {inference.camera_id.name}")
    print(f"Confidence: {inference.confidence}")
    print(f"Alert: {inference.alert.id if inference.alert else 'None'}")
```

### Get Active Suspicious Tracks
```python
from apps.ai_engine.models import DetectionTrack

suspicious = DetectionTrack.objects.filter(
    is_suspicious=True,
    is_active=True
).order_by('-ml_theft_score')

for track in suspicious:
    print(f"Track {track.track_id} on {track.camera_id.name}")
    print(f"Score: {track.ml_theft_score}")
```

## 🔧 Troubleshooting

### Models Not Loading
```bash
# Check model files exist
ls ModelExport/yolov8l.pt
ls ModelExport/yolov8l-pose.pt
ls ModelExport/trained_models/theft_classifier.pkl
```

### Low FPS / Slow Processing
```python
# Check device
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))

# If False, install CUDA-enabled PyTorch:
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Frame Encoding Issues
```python
# Correct way to encode frame:
import cv2
import base64

frame = cv2.imread("image.jpg")
_, buffer = cv2.imencode('.jpg', frame)
frame_b64 = base64.b64encode(buffer).decode('utf-8')

# Don't include data URL prefix in API calls
# The API will handle it if present
```

## 📞 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ai/analyze-frame/` | POST | Process base64 frame |
| `/api/ai/process-camera/` | POST | Capture & process from camera |
| `/api/ai/full-pipeline/` | POST | Flexible endpoint (frame or camera) |
| `/api/ai/model-info/` | GET | Get model information |
| `/api/ai/inference-history/` | GET | Query inference results |
| `/api/ai/health/` | GET | Check service health |

## ✅ Verification Checklist

- [ ] Server starts without errors
- [ ] Health check returns "healthy"
- [ ] Model info shows all models loaded
- [ ] Can analyze test frame
- [ ] Theft detection creates alerts
- [ ] Database migrations applied
- [ ] JWT authentication works

## 🎉 You're Ready!

Your AI pipeline is now integrated and ready for production use!

