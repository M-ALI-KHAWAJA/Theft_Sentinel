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

