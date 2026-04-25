# AI Engine Integration Documentation

## 🎯 Overview

The AI Engine is fully integrated into the Django REST Framework backend. It runs the YOLOv8 + DeepSORT + ML classifier pipeline either **on-demand** (single frame analysis) or **continuously** (live camera stream monitoring with automatic theft-alert video clip generation and Cloudinary upload).

The integration is **fully isolated**, **non-destructive**, and **production-ready**.

---

## 📁 Project Structure

```
theft_sentinel_backend/
├── apps/
│   ├── ai_engine/                    # Isolated AI module
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── serializers.py       # API request/response serializers
│   │   │   ├── views.py             # All API endpoint handlers (9 views)
│   │   │   └── urls.py              # 9 API routes
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py        # AI model lifecycle manager (lazy loader)
│   │   │   ├── clip_encoding.py     # NEW — H.264 MP4 frame → file encoder
│   │   │   ├── continuous_monitor.py # NEW — live stream monitor + clip upload
│   │   │   └── inference_runner.py  # Wraps YOLOv8/DeepSORT/ML pipeline
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── frame_utils.py       # Base64 decode / RTSP capture / validate
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py                # AIInference, DetectionTrack
│   │   ├── tests.py
│   │   └── README.md
│   ├── alerts/
│   │   ├── cloudinary_video.py      # NEW — Cloudinary upload/delete helpers
│   │   ├── models.py                # Alert + video_url / video_public_id fields
│   │   ├── serializers.py
│   │   ├── signals.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── accounts/                    # JWT auth + RBAC (unchanged)
│   ├── cameras/                     # Camera model + RTSP URLs (unchanged)
│   ├── incidents/                   # Incident model (unchanged)
│   ├── tracking/                    # Tracking ingest API (unchanged)
│   ├── dashboard/
│   ├── feedback/
│   ├── mobile/
│   ├── personnel/
│   └── surveillance/
├── ModelExport/                      # AI pipeline (UNTOUCHED)
│   ├── ml_classifier/
│   │   ├── feature_builder.py
│   │   ├── sequence_collector.py
│   │   └── theft_classifier.py
│   ├── trained_models/
│   │   └── theft_classifier.pkl
│   ├── YOLOv8l_YOLOv8l_Pose_DeepSort_MLclassifier.py
│   ├── yolov8l-pose.pt
│   └── yolov8l.pt
├── config/
│   └── urls.py                      # All app routes registered
├── .env                             # Environment variables (see section below)
```

---

## 🚀 API Endpoints

All endpoints are prefixed with `/api/ai/`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/analyze-frame/` | ✅ JWT | Analyze single base64-encoded frame |
| `POST` | `/process-camera/` | ✅ JWT | Capture frame from camera RTSP stream and analyze |
| `POST` | `/full-pipeline/` | ✅ JWT | Combined endpoint — accepts `frame` OR `camera_id` |
| `POST` | `/monitor/start/` | ✅ JWT | Start continuous monitoring on a live camera stream |
| `POST` | `/monitor/stop/` | ✅ JWT | Stop continuous monitoring |
| `GET`  | `/monitor/status/` | ✅ JWT | Get status of all running monitors (or single) |
| `GET`  | `/model-info/` | ✅ JWT | Get AI model metadata and device info |
| `GET`  | `/inference-history/` | ✅ JWT | Paginated inference logs with filters |
| `GET`  | `/health/` | 🌐 Public | Health check — no auth required |

---

### 1. Analyze Frame

**POST** `/api/ai/analyze-frame/`

```json
{
  "frame": "base64_encoded_image_data",
  "camera_id": "optional_camera_objectid",
  "save_to_db": true,
  "create_alert_on_theft": true
}
```

**Response:**
```json
{
  "classification": "theft",
  "confidence": 0.87,
  "persons": 2,
  "objects": 5,
  "tracks": 2,
  "processing_time_ms": 145.2,
  "camera_name": "Entrance Cam",
  "camera_location": "Front Gate",
  "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0",
  "alert_created": true,
  "alert_id": "65f3a2b1c8d4e5f6a7b8c9d1",
  "inference_id": "65f3a2b1c8d4e5f6a7b8c9d2",
  "detections": [...],
  "poses": [...],
  "tracks_data": [...],
  "suspicious_tracks": [...],
  "frame_metadata": {...}
}
```

---

### 2. Process Camera

**POST** `/api/ai/process-camera/`

Captures one frame from the camera's RTSP URL, then runs the full pipeline.

```json
{
  "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0",
  "save_to_db": true,
  "create_alert_on_theft": true
}
```

**Response:** Same structure as `analyze-frame`.

---

### 3. Full Pipeline

**POST** `/api/ai/full-pipeline/`

Convenience endpoint — routes to `analyze-frame` if `frame` key is present, otherwise routes to `process-camera`.

---

### 4. Start Continuous Monitor

**POST** `/api/ai/monitor/start/`

Starts a background thread that reads the camera's RTSP stream at full FPS, runs the AI pipeline on every frame, writes results to the DB every ~2 seconds (or immediately on theft), and triggers the video clip workflow on theft detection.

```json
{
  "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0",
  "restart": false
}
```

**Response (success):**
```json
{
  "success": true,
  "message": "Started continuous monitoring",
  "already_running": false,
  "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0",
  "camera_name": "Entrance Cam",
  "rtsp_url_preview": "rtsp://admin:pass@192.168.1.10:554/..."
}
```

---

### 5. Stop Continuous Monitor

**POST** `/api/ai/monitor/stop/`

```json
{
  "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0"
}
```

---

### 6. Monitor Status

**GET** `/api/ai/monitor/status/?camera_id=<optional>`

```json
{
  "monitors": {
    "65f3a2b1c8d4e5f6a7b8c9d0": {
      "camera_id": "65f3a2b1c8d4e5f6a7b8c9d0",
      "is_running": true,
      "frames_processed": 4521,
      "fps": 27.3,
      "elapsed_seconds": 165.6,
      "error_count": 0,
      "last_result": { "classification": "normal", "confidence": 0.12 }
    }
  },
  "total_monitors": 1
}
```

---

### 7. Model Info

**GET** `/api/ai/model-info/`

```json
{
  "detection_model": "ModelExport/yolov8l.pt",
  "pose_model": "ModelExport/yolov8l-pose.pt",
  "ml_classifier": "ModelExport/trained_models/theft_classifier.pkl",
  "device": "cuda:0",
  "cuda_available": true,
  "models_loaded": true,
  "ml_classifier_loaded": true
}
```

---

### 8. Inference History

**GET** `/api/ai/inference-history/`

Query params: `camera_id`, `classification`, `min_confidence`, `limit` (default 50, max 500)

---

### 9. Health Check

**GET** `/api/ai/health/` — No auth required.

```json
{
  "status": "healthy",
  "models_loaded": true,
  "device": "cuda:0"
}
```

---

## 🎬 Video Clip Pipeline (Theft Alert)

When the continuous monitor detects a theft, it automatically:

1. **Snapshots the rolling frame buffer** — a `deque(maxlen=150)` that holds ~5 seconds of frames at 30 FPS.
2. **Encodes an MP4 clip** using `services/clip_encoding.py`:
   - Codec: H.264 (`avc1` → `H264` → `X264` → `mp4v` fallback)
   - Max width: 1280px (auto-downscaled)
   - Duration: up to 5 seconds (minimum 8 frames)
3. **Uploads to Cloudinary** via `apps/alerts/cloudinary_video.py`.
4. **Saves `video_url` and `video_public_id`** back to the `Alert` row.
5. Runs entirely in a **daemon thread** so the monitoring loop is never blocked.

### Alert Model Fields (Updated)

```python
class Alert(models.Model):
    id              = ObjectIdAutoField(primary_key=True)
    camera_id       = ForeignKey('cameras.Camera', ...)
    alert_type      = CharField(max_length=100)          # e.g. 'THEFT_DETECTED'
    severity        = CharField(max_length=50)           # 'HIGH' | 'MEDIUM'
    timestamp       = DateTimeField(default=timezone.now)
    status          = CharField(...)                     # 'ACTIVE' | 'ACKED' | 'RESOLVED'
    metadata        = JSONField(default=dict)            # confidence, tracks, FPS, etc.
    video_url       = URLField(null=True, blank=True)    # Cloudinary secure URL
    video_public_id = CharField(null=True, blank=True)  # Cloudinary public_id (for deletion)
```

### Cloudinary Helper Functions (`apps/alerts/cloudinary_video.py`)

| Function | Description |
|----------|-------------|
| `upload_video_to_cloudinary(file_path)` | Upload MP4, returns `(secure_url, public_id)` |
| `upload_video_file(file_path)` | Backward-compatible wrapper, returns `secure_url` only |
| `delete_cloudinary_video(public_id)` | Delete by known `public_id` |
| `delete_cloudinary_video_from_url(url)` | Derive `public_id` from URL then delete |
| `public_id_from_video_url(url)` | Extract `public_id` from Cloudinary URL |

Credentials are read from **Django settings** first, falling back to `os.environ`.

---

## 🔗 Integration with Existing Code

### Alert Creation Flow

When `classification == "theft"` the monitor calls `_create_alert()`:

```python
alert = Alert.objects.create(
    camera_id=camera,
    alert_type='THEFT_DETECTED',
    severity='HIGH' if confidence > 0.7 else 'MEDIUM',
    status='ACTIVE',
    metadata={
        'confidence': ...,
        'suspicious_tracks': [...],
        'num_detections': ...,
        'num_persons': ...,
        'detected_by': 'CONTINUOUS_MONITOR',
        'detection_timestamp': ...,
        'fps': ...,
    }
)
# Then triggers video clip upload in a daemon thread
self._try_upload_alert_clip(alert)
```

The on-demand views (`AnalyzeFrameView`, `ProcessCameraView`) create alerts via the existing `AlertCreateSerializer`.

### Existing Code — NOT Modified

- `apps/accounts/*` — authentication & RBAC
- `apps/alerts/models.py` / `views.py` / `serializers.py` / `signals.py` — existing alert logic
- `apps/incidents/*` — incident management
- `apps/cameras/*` — camera model & RTSP URLs
- `apps/tracking/*` — tracking ingest
- `ModelExport/*` — entire AI pipeline

### Modified / Added

| File | Change |
|------|--------|
| `apps/alerts/models.py` | Added `video_url`, `video_public_id` fields |
| `apps/alerts/cloudinary_video.py` | **NEW** — Cloudinary upload/delete helpers |
| `apps/ai_engine/services/continuous_monitor.py` | **NEW** — `ContinuousMonitor`, `MonitorManager` |
| `apps/ai_engine/services/clip_encoding.py` | **NEW** — `write_frames_to_mp4()` |
| `apps/ai_engine/api/views.py` | Added `StartContinuousMonitorView`, `StopContinuousMonitorView`, `MonitorStatusView` |
| `apps/ai_engine/api/urls.py` | Added 3 monitor routes |
| `config/urls.py` | Added `path('api/ai/', include('apps.ai_engine.api.urls'))` |

---

## 🗄️ Database Models

### AIInference (`ai_inferences` collection)

| Field | Type | Description |
|-------|------|-------------|
| `id` | ObjectIdAutoField | MongoDB ObjectId primary key |
| `camera_id` | FK → Camera | Source camera (nullable) |
| `detections` | JSONField | YOLOv8 detected bounding boxes |
| `poses` | JSONField | YOLOv8-Pose keypoints |
| `tracks` | JSONField | DeepSORT track data |
| `classification` | CharField | `"theft"` or `"normal"` |
| `confidence` | FloatField | ML classifier score (0–1) |
| `frame_metadata` | JSONField | Frame-level stats |
| `processing_time_ms` | FloatField | Inference duration |
| `alert` | FK → Alert | Linked alert (if theft) |
| `timestamp` | DateTimeField | When inference ran |

### DetectionTrack (`detection_tracks` collection)

| Field | Type | Description |
|-------|------|-------------|
| `id` | ObjectIdAutoField | |
| `camera_id` | FK → Camera | |
| `track_id` | IntegerField | DeepSORT track ID |
| `object_type` | CharField | `"person"`, `"bag"`, `"object"` |
| `first_seen`, `last_seen` | DateTimeField | Track timestamps |
| `frame_count` | IntegerField | |
| `hand_in_bag_frames` | IntegerField | Behavioral counter |
| `hand_in_torso_frames` | IntegerField | Behavioral counter |
| `fast_wrist_frames` | IntegerField | Behavioral counter |
| `near_object_frames` | IntegerField | Behavioral counter |
| `concealment_events` | IntegerField | Suspicious action count |
| `ml_theft_score` | FloatField | Latest prediction |
| `max_theft_score` | FloatField | Peak prediction |
| `is_suspicious`, `is_active` | BooleanField | Status flags |

---

## 🔧 Setup & Installation

### 1. Dependencies (`newReq.txt`)

```
django
djangorestframework
torch
ultralytics
opencv-python
deep-sort-realtime
scikit-learn
joblib
cloudinary        # For video clip upload
python-dotenv
```

### 2. Environment Variables (`.env`)

```bash
# Django
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Atlas
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=theft_sentinel

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Twilio (SMS)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# Cloudinary (video clip storage)
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

### 3. Database Migration

```bash
python manage.py migrate ai_engine
python manage.py migrate alerts   # picks up video_url / video_public_id
```

### 4. Start Server

```bash
python manage.py runserver
# AI models load automatically on startup
```

### 5. Verify

```bash
curl http://localhost:8000/api/ai/health/
# Expected: {"status":"healthy","models_loaded":true,"device":"cuda:0"}
```

---

## 🔐 Security & Permissions

All endpoints require JWT authentication (`Authorization: Bearer <token>`) except `/api/ai/health/`.

| Role | AI Endpoints | Monitor Control | Inference History |
|------|-------------|----------------|-------------------|
| Admin | ✅ Full | ✅ Full | ✅ Full |
| Security In-Charge | ✅ Full | ✅ Full | ✅ Full |
| Security Guard | ✅ Read | ❌ | ✅ Read |

---

## 📈 Performance

| Mode | Expected Time (GPU) |
|------|-------------------|
| Detection only | 30–50 ms |
| Detection + Pose | 80–120 ms |
| Full pipeline (Detection + Pose + ML) | 100–150 ms |
| CPU mode | 2–5× slower |

**Continuous Monitor:**
- Processes at full stream FPS (15–30)
- DB write every ~2 s (60 frames at 30 FPS) or immediately on theft
- Clip encoding + Cloudinary upload in non-blocking daemon thread
- Auto-reconnect after 10 consecutive read errors

**Clip Encoding:**
- Max clip width: 1280 px
- FPS: clamped to 8–60; falls back to 25 if stream FPS < 5
- Codec: H.264 (`avc1` preferred, browser-compatible)

---

## 🐛 Troubleshooting

### AI Models Not Loading

**Error:** `"AI service not initialized"`

1. Check `ModelExport/` directory exists with all three model files:
   - `yolov8l.pt`
   - `yolov8l-pose.pt`
   - `trained_models/theft_classifier.pkl`
2. Run `python manage.py runserver` and watch logs.

### CUDA Not Available

**Error:** `"CUDA not available. Using CPU"`

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Frame Decoding Error

**Error:** `"Failed to decode frame from base64"`

- Ensure base64 string is valid (strip `data:image/...;base64,` prefix if present).
- Use JPEG or PNG images.

### Cloudinary Clip Not Uploading

1. Verify `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` are set.
2. Check server logs for `clip-upload-<alert_id>` thread errors.
3. Confirm `pip install cloudinary` is installed.

### Monitor Not Starting

1. Verify camera RTSP URL is reachable: `cv2.VideoCapture(rtsp_url).isOpened()`.
2. Check AI service is ready: `GET /api/ai/health/`.
3. Look for `"Failed to open stream"` in logs.

### Alert Has No `video_url`

- Frame buffer may have been empty at the moment of detection (monitor just started).
- Cloudinary upload failed — check daemon thread logs.
- The clip upload is asynchronous; `video_url` is patched in a few seconds after the alert is created.

---

## ✅ Integration Checklist

- [x] AI models load automatically on server startup
- [x] 9 API endpoints functional
- [x] On-demand frame analysis (`analyze-frame`, `process-camera`, `full-pipeline`)
- [x] Continuous live stream monitoring (`monitor/start`, `monitor/stop`, `monitor/status`)
- [x] 5-second rolling frame buffer per monitor
- [x] Theft → MP4 clip encoded in-memory
- [x] MP4 clip uploaded to Cloudinary (non-blocking)
- [x] `video_url` + `video_public_id` saved to `Alert` row
- [x] Alert creation via existing `AlertCreateSerializer`
- [x] `AIInference` and `DetectionTrack` DB models migrated
- [x] RBAC permissions enforced on all endpoints
- [x] Auto-reconnect on stream failures
- [x] Admin interface configured
- [x] Test suite provided (`test_ai_engine.py`)
- [x] Zero modifications to existing business logic

---

## 🎉 What Was Changed vs. Original Integration

| Area | Original | Current |
|------|----------|---------|
| AI endpoints | 6 | 9 (added monitor start/stop/status) |
| Services | `ai_service.py`, `inference_runner.py` | + `continuous_monitor.py`, `clip_encoding.py` |
| Alert model | No video fields | `video_url`, `video_public_id` added |
| Cloudinary | Not integrated | `apps/alerts/cloudinary_video.py` |
| Frame buffer | None | 150-frame rolling deque (~5 s at 30 FPS) |
| Clip pipeline | None | encode → upload → save URL (async) |
| Monitoring | Poll-based (2-s intervals) | Continuous full-FPS stream |

---

## 📞 Support

1. Check this documentation
2. Check server logs (`python manage.py runserver`)
3. Test health: `GET /api/ai/health/`
4. Test monitor status: `GET /api/ai/monitor/status/`
5. Verify model files in `ModelExport/`
6. Verify Cloudinary credentials in `.env`
