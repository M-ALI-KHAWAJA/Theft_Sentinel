# Theft Sentinel API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints (except register and login) require JWT authentication.

Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication Endpoints

### Register User
**POST** `/auth/register/`

**Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123",
  "password2": "securepass123",
  "role": "GUARD"
}
```

**Response (201):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "GUARD",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  },
  "message": "User registered successfully"
}
```

### Login
**POST** `/auth/login/`

**Body:**
```json
{
  "username": "john_doe",
  "password": "securepass123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "GUARD",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

### Refresh Token
**POST** `/auth/refresh/`

**Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Logout
**POST** `/auth/logout/`

**Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

---

## 2. Camera Endpoints

### List Cameras
**GET** `/cameras/`

**Query Parameters:**
- `zone` (optional): Filter by zone
- `status` (optional): Filter by status (ONLINE/OFFLINE)

**Response (200):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Main Entrance Camera",
      "rtsp_url": "rtsp://192.168.1.100:554/stream",
      "location": "Building A - Main Entrance",
      "zone": "Zone A",
      "status": "ONLINE",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

### Create Camera
**POST** `/cameras/` (Admin only)

**Body:**
```json
{
  "name": "Main Entrance Camera",
  "rtsp_url": "rtsp://192.168.1.100:554/stream",
  "location": "Building A - Main Entrance",
  "zone": "Zone A",
  "status": "ONLINE"
}
```

### Update Camera Status
**PATCH** `/cameras/{id}/status/`

**Body:**
```json
{
  "status": "OFFLINE"
}
```

---

## 3. Alert Endpoints

### List Alerts
**GET** `/alerts/`

**Query Parameters:**
- `status` (optional): ACTIVE, ACKED, RESOLVED
- `camera_id` (optional): Filter by camera
- `alert_type` (optional): Filter by type
- `start_date` (optional): ISO format
- `end_date` (optional): ISO format

**Response (200):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "camera_id": 1,
      "camera_details": {
        "id": 1,
        "name": "Main Entrance Camera",
        "location": "Building A - Main Entrance"
      },
      "alert_type": "theft_detected",
      "severity": "HIGH",
      "timestamp": "2024-01-01T14:30:00Z",
      "status": "ACTIVE",
      "metadata": {
        "confidence": 0.95,
        "frame_url": "http://..."
      }
    }
  ]
}
```

### Acknowledge Alert
**PATCH** `/alerts/{id}/acknowledge/`

**Body:**
```json
{
  "status": "ACKED"
}
```

### Get Active Alerts
**GET** `/alerts/active/`

---

## 4. Incident Endpoints

### List Incidents
**GET** `/incidents/`

**Query Parameters:**
- `status` (optional): CREATED, ASSIGNED, ACKNOWLEDGED, RESOLVED
- `assigned_to` (optional): User ID
- `my_incidents` (optional): "true" to get only your incidents

**Response (200):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "alert_id": 1,
      "alert_details": {
        "id": 1,
        "alert_type": "theft_detected",
        "severity": "HIGH"
      },
      "assigned_to": 2,
      "assigned_to_details": {
        "id": 2,
        "username": "guard_john",
        "role": "GUARD"
      },
      "status": "ASSIGNED",
      "notes": "Investigating the incident",
      "created_at": "2024-01-01T14:35:00Z",
      "updated_at": "2024-01-01T15:00:00Z"
    }
  ]
}
```

### Assign Incident
**PATCH** `/incidents/{id}/assign/`

**Body:**
```json
{
  "assigned_to": 2,
  "notes": "Assigning to guard on duty"
}
```

### Update Incident Status
**PATCH** `/incidents/{id}/status/`

**Body:**
```json
{
  "status": "ACKNOWLEDGED",
  "notes": "On-site, investigating"
}
```

---

## 5. Surveillance Endpoints

### Ingest AI Event
**POST** `/surveillance/ingest/`

**Body:**
```json
{
  "camera_id": 1,
  "event_type": "theft_detected",
  "frame_url": "http://storage.example.com/frames/frame123.jpg",
  "ai_data": {
    "confidence": 0.95,
    "bounding_boxes": [[100, 200, 300, 400]],
    "detected_objects": ["person", "bag"]
  }
}
```

**Response (201):**
```json
{
  "surveillance_event": {
    "id": 1,
    "camera_id": 1,
    "event_type": "theft_detected",
    "frame_url": "http://...",
    "ai_data": {...},
    "created_at": "2024-01-01T14:30:00Z"
  },
  "alert_created": true,
  "incident_created": true,
  "alert": {...},
  "incident": {...}
}
```

---

## 6. Tracking Endpoints

### Ingest Tracking Data
**POST** `/tracking/ingest/`

**Body:**
```json
{
  "camera_id": 1,
  "vector": [0.123, 0.456, 0.789, ...],
  "person_id": "PERSON_abc123"
}
```

**Note:** If `person_id` is not provided, it will be auto-generated.

### Get Person Tracking Path
**GET** `/tracking/person/{person_id}/path/`

**Query Parameters:**
- `time_window` (optional): Time window in minutes (default: 60)

**Response (200):**
```json
{
  "person_id": "PERSON_abc123",
  "time_window_minutes": 60,
  "tracking_path": [
    {
      "camera_id": 1,
      "camera_name": "Main Entrance",
      "location": "Building A",
      "timestamp": "2024-01-01T14:00:00Z"
    },
    {
      "camera_id": 3,
      "camera_name": "Corridor Camera",
      "location": "Building A - Corridor",
      "timestamp": "2024-01-01T14:05:00Z"
    }
  ],
  "total_locations": 2
}
```

---

## 7. Mobile/Notification Endpoints

### Send SMS
**POST** `/mobile/send-sms/` (Admin/Incharge only)

**Body:**
```json
{
  "phone_number": "+1234567890",
  "message": "Alert: Theft detected at Main Entrance"
}
```

### Send Email
**POST** `/mobile/send-email/` (Admin/Incharge only)

**Body:**
```json
{
  "email_address": "guard@example.com",
  "subject": "Security Alert",
  "message": "Alert: Theft detected at Main Entrance at 14:30"
}
```

### Send Bulk Notification
**POST** `/mobile/send-bulk/` (Admin/Incharge only)

**Body:**
```json
{
  "user_ids": [1, 2, 3],
  "subject": "System Alert",
  "message": "Multiple alerts detected in Zone A",
  "send_sms": true,
  "send_email": true
}
```

---

## 8. Dashboard Endpoints

### Dashboard Overview
**GET** `/dashboard/overview/`

**Response (200):**
```json
{
  "cameras": {
    "total": 10,
    "online": 8,
    "offline": 2,
    "online_percentage": 80.0
  },
  "alerts": {
    "total": 150,
    "active": 5,
    "today": 12,
    "this_week": 45,
    "by_severity": {
      "HIGH": 20,
      "MEDIUM": 80,
      "LOW": 50
    }
  },
  "incidents": {
    "total": 50,
    "active": 3,
    "resolved": 45,
    "today": 2,
    "by_status": {
      "CREATED": 2,
      "ASSIGNED": 1,
      "ACKNOWLEDGED": 0,
      "RESOLVED": 45
    },
    "resolution_rate": 90.0
  },
  "personnel": {
    "total_personnel": 15,
    "total_users": 20
  },
  "surveillance_events": {
    "today": 50,
    "this_week": 300
  },
  "timestamp": "2024-01-01T15:00:00Z"
}
```

### Alert Statistics
**GET** `/dashboard/alerts-stats/`

**Query Parameters:**
- `days` (optional): Number of days (default: 30)

### Incident Statistics
**GET** `/dashboard/incidents-stats/`

**Query Parameters:**
- `days` (optional): Number of days (default: 30)

### Recent Activity
**GET** `/dashboard/recent-activity/`

**Query Parameters:**
- `limit` (optional): Number of items (default: 20)

---

## 9. Feedback Endpoints

### Submit Feedback
**POST** `/feedback/`

**Body:**
```json
{
  "type": "FALSE_POSITIVE",
  "message": "The alert at 14:30 was a false positive - it was a maintenance worker."
}
```

**Types:** `GENERAL`, `INCIDENT`, `FALSE_POSITIVE`, `TRUE_POSITIVE`

### List My Feedback
**GET** `/feedback/me/`

### Feedback Statistics
**GET** `/feedback/stats/` (Admin only)

---

## 10. AI Engine Endpoints

Base prefix: `/api/ai/`

> All AI endpoints require `Authorization: Bearer <access_token>` **except**
> the SSE real-time tracking stream and the health check, which are public so
> the browser can open them without custom headers.

### Analyze Single Frame
**POST** `/ai/analyze-frame/`

**Body:**
```json
{
  "frame": "<base64-encoded JPEG>",
  "camera_id": "abc123",
  "create_alert_on_theft": true,
  "save_to_db": true
}
```

**Response (200):**
```json
{
  "classification": "theft",
  "confidence": 0.87,
  "persons": 2,
  "tracks": 2,
  "alert_created": true,
  "alert_id": "...",
  "tracks_data": [...],
  "suspicious_tracks": [...]
}
```

---

### Process Camera Frame
**POST** `/ai/process-camera/`

Captures a live frame from the camera's RTSP URL and runs inference.

**Body:**
```json
{ "camera_id": "abc123" }
```

**Response:** Same structure as `/ai/analyze-frame/`.

---

### Full Pipeline (combined)
**POST** `/ai/full-pipeline/`

Accepts either `frame` (base64) or `camera_id`.

---

### Start Continuous Monitor
**POST** `/ai/monitor/start/`

Starts a background thread that processes the live camera stream at up to
30 FPS and publishes results to SSE clients.

**Body:**
```json
{ "camera_id": "abc123", "restart": false }
```

**Response (200):**
```json
{
  "success": true,
  "message": "Started continuous monitoring",
  "camera_id": "abc123",
  "camera_name": "Entrance Cam"
}
```

---

### Stop Continuous Monitor
**POST** `/ai/monitor/stop/`

**Body:**
```json
{ "camera_id": "abc123" }
```

**Response (200):**
```json
{ "success": true, "message": "Stopped monitoring", "camera_id": "abc123" }
```

---

### Monitor Status
**GET** `/ai/monitor/status/?camera_id=abc123`

Returns processing stats (FPS, frames processed, last result) for one or all
running monitors.

**Response (200):**
```json
{
  "monitors": {
    "abc123": {
      "camera_id": "abc123",
      "is_running": true,
      "frames_processed": 1523,
      "fps": 28.5,
      "elapsed_seconds": 53.4,
      "error_count": 0,
      "last_result": { "classification": "normal", "confidence": 0.12 }
    }
  },
  "total_monitors": 1
}
```

---

### Real-Time Tracking SSE Stream *(Canvas Overlay)*
**GET** `/api/ai/cameras/<camera_id>/realtime-tracking/`

**Authentication:** None required (public — same policy as the MJPEG feed).
Open with the browser's native `EventSource` API.

**Protocol:** Server-Sent Events (`text/event-stream`).  
The connection stays open indefinitely.  A `: keepalive` comment is sent
every 25 seconds when there is no new tracking data so proxies do not
time-out the connection.

**Usage flow:**
1. Start the continuous monitor for the camera (`POST /api/ai/monitor/start/`).
2. Connect to this SSE endpoint — the frontend receives tracking payloads in
   real time and draws bounding boxes on an HTML5 `<canvas>` overlaid on the
   raw MJPEG feed.

**Initial handshake event** (sent once on connection):
```
data: {"type": "connected", "camera_id": "abc123"}
```

**Tracking event** (sent at up to 10 FPS while the monitor is running):
```
data: {
  "camera_id":      "abc123",
  "timestamp":      "2026-04-22T10:00:00.123Z",
  "frame_width":    1280,
  "frame_height":   720,
  "tracks": [
    {
      "track_id":   1,
      "global_id":  5,
      "bbox":       [120, 45, 260, 380],
      "x3d_score":  0.87,
      "confidence": 0.93
    }
  ],
  "suspicious_ids":  [1],
  "alert_triggered": true,
  "classification":  "theft",
  "confidence":      0.87
}
```

**Field descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `camera_id` | string | Camera database ID |
| `timestamp` | ISO-8601 string | Server-side timestamp of the processed frame |
| `frame_width` | **integer** | **Native width** of the video frame that the AI pipeline processed (e.g. 1280). Source: `frame.shape[1]` in OpenCV. Required by the frontend to scale bbox coordinates. |
| `frame_height` | **integer** | **Native height** of the video frame that the AI pipeline processed (e.g. 720). Source: `frame.shape[0]` in OpenCV. Required by the frontend to scale bbox coordinates. |
| `tracks` | array | All active DeepSORT tracks in this frame |
| `tracks[].track_id` | integer | Short-lived DeepSORT track ID (resets if track is lost) |
| `tracks[].global_id` | integer | Cross-camera Re-ID global identity (persistent) |
| `tracks[].bbox` | `[x1, y1, x2, y2]` | Bounding box **in native frame pixel coordinates** — must be scaled before drawing (see formula below) |
| `tracks[].x3d_score` | float 0–1 | X3D activity score: ≥ 0.50 = suspicious, ≥ 0.80 = theft |
| `tracks[].confidence` | float 0–1 | YOLO detection confidence for this person |
| `suspicious_ids` | integer[] | `track_id` values whose `x3d_score ≥ 0.50` |
| `alert_triggered` | boolean | `true` when `classification == "theft"` (x3d_score ≥ 0.80) |
| `classification` | string | `"theft"` or `"normal"` |
| `confidence` | float | Highest X3D score across all tracks in this frame |

> **Important — Resolution Bridge:**  
> `frame_width` / `frame_height` are the dimensions of the frame that was
> passed to YOLO/DeepSORT.  The displayed video element may be a different
> size (e.g. 640 CSS px wide for a 1280-px native frame).  
> The frontend **must** scale every bbox coordinate before drawing.

**Coordinate scaling — exact frontend formula:**
```javascript
// 1. Get the CSS-rendered size of the canvas element
const scaleX = canvas.clientWidth  / frame_width;   // e.g. 640 / 1280 = 0.5
const scaleY = canvas.clientHeight / frame_height;  // e.g. 360 / 720  = 0.5

// 2. Map native bbox coords → canvas draw coords
const drawX = bbox[0] * scaleX;           // x1
const drawY = bbox[1] * scaleY;           // y1
const drawW = (bbox[2] - bbox[0]) * scaleX;  // width
const drawH = (bbox[3] - bbox[1]) * scaleY;  // height

// 3. Draw
ctx.strokeRect(drawX, drawY, drawW, drawH);
```

> `canvas.clientWidth` / `canvas.clientHeight` reflect the CSS-rendered
> pixel dimensions of the `<canvas>` element.  Using these (rather than
> `canvas.width` / `canvas.height`, which are the internal buffer dimensions)
> ensures the formula remains correct regardless of how the page is laid out.

**Drawing condition (frontend):**

The canvas should redraw on every animation frame when:
```
alert_triggered === true  OR  suspicious_ids.length > 0
```

Only tracks whose `track_id` appears in `suspicious_ids`, **or** whose
`x3d_score ≥ 0.50` while `alert_triggered` is `true`, should have a box
drawn.

**"Stop Tracking" interaction:**  
The frontend exposes a "Stop Tracking" button that appears only when
`alert_triggered` is `true`.  Clicking it sets a `manualOverride` flag that
stops canvas drawing immediately (without disconnecting the SSE stream).
The flag resets automatically when `alert_triggered` returns to `false` on
the next SSE event.

**z-index layering:**
```
<img>    z-index: 1   (raw video — background)
<canvas> z-index: 10  (overlay — pointer-events: none so clicks pass through)
buttons  z-index: 20  (interactive UI on top of both)
```

**Error (404) — camera not found:**
```json
{ "error": "Camera abc123 not found" }
```

---

### Model Info
**GET** `/ai/model-info/`

Returns the names and load status of YOLO, OSNet, and X3D models.

---

### Inference History
**GET** `/ai/inference-history/?camera_id=abc123&classification=theft&limit=50`

---

### AI Health Check
**GET** `/ai/health/`  *(public)*

```json
{ "status": "healthy", "models_loaded": true, "device": "cuda" }
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid data",
  "details": {...}
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

---

## Role Permissions Summary

| Endpoint | ADMIN | SECURITY_INCHARGE | GUARD |
|----------|-------|-------------------|-------|
| Auth | ✅ | ✅ | ✅ |
| Cameras (Read) | ✅ | ✅ | ✅ |
| Cameras (Write) | ✅ | ❌ | ❌ |
| Alerts (Read) | ✅ | ✅ | ✅ |
| Alerts (Acknowledge) | ✅ | ✅ | ❌ |
| Incidents (Read All) | ✅ | ✅ | Own only |
| Incidents (Assign) | ✅ | ✅ | ❌ |
| Notifications | ✅ | ✅ | ❌ |
| Dashboard | ✅ | ✅ | ✅ |
| Feedback | ✅ | ✅ | ✅ |

---

For more details, see the main README.md file.

