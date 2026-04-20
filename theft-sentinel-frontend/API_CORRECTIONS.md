# API Corrections Summary

All API requests have been corrected to match the official backend schema. This document outlines all changes made.

## ✅ Fixed Issues

### 🔴 Common Issues Found & Fixed:
1. **Wrong HTTP methods** (POST instead of PATCH)
2. **Wrong field names** (guard_id → assigned_to, resolution → notes)
3. **Extra non-existent endpoints** removed
4. **Missing required body parameters** added
5. **Query params** properly documented

---

## 📋 Corrected API Endpoints

### 1️⃣ AUTH (`/api/auth/`)

#### ✅ POST `/api/auth/register/`
```javascript
// Body (all required)
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password2": "string",
  "role": "ADMIN" | "SECURITY_INCHARGE" | "GUARD"
}
```

#### ✅ POST `/api/auth/login/`
```javascript
// Body
{
  "username": "string",
  "password": "string"
}
```

#### ✅ Headers for Authenticated Routes
```javascript
Authorization: Bearer <access_token>
```

---

### 2️⃣ CAMERAS (`/api/cameras/`)

#### ✅ GET `/api/cameras/`
**Query params:**
- `?zone=Zone_A`
- `?status=ONLINE`

#### ✅ POST `/api/cameras/`
```javascript
// Body
{
  "name": "string",
  "rtsp_url": "string",
  "location": "string",
  "zone": "string",
  "status": "ONLINE" | "OFFLINE"
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/cameras/by-zone/`
- `/api/cameras/active/`
- `/api/cameras/{id}/status/`

---

### 3️⃣ ALERTS (`/api/alerts/`)

#### ✅ GET `/api/alerts/`
**Query params:**
- `?status=ACTIVE`
- `?camera_id=1`
- `?alert_type=string`
- `?severity=HIGH`

#### ✅ POST `/api/alerts/`
```javascript
// Body
{
  "camera_id": 1,
  "alert_type": "string",
  "severity": "HIGH" | "MEDIUM" | "LOW",
  "metadata": {
    "confidence": 0.95,
    "frame_url": "string"
  }
}
```

#### 🔧 CORRECTED: PATCH `/api/alerts/{id}/acknowledge/`
**Changed from:** `POST` → **PATCH**
```javascript
// Body
{
  "status": "ACKED" | "RESOLVED"
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/alerts/active/`
- `/api/alerts/recent/`
- `/api/alerts/by-severity/`

---

### 4️⃣ INCIDENTS (`/api/incidents/`)

#### ✅ GET `/api/incidents/`
**Query params:**
- `?status=ASSIGNED`
- `?assigned_to=2`
- `?my_incidents=true`

#### ✅ POST `/api/incidents/`
```javascript
// Body
{
  "alert_id": 1,
  "assigned_to": 2,
  "notes": "string"
}
```

#### 🔧 CORRECTED: PATCH `/api/incidents/{id}/assign/`
**Changed from:** `POST` with `guard_id` → **PATCH** with `assigned_to`
```javascript
// Body
{
  "assigned_to": 3,
  "notes": "string"
}
```

#### 🔧 CORRECTED: PATCH `/api/incidents/{id}/status/`
**Changed from:** `resolution` field → **notes** field
```javascript
// Body
{
  "status": "CREATED" | "ASSIGNED" | "ACKNOWLEDGED" | "RESOLVED",
  "notes": "string"
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/incidents/my-incidents/`
- `/api/incidents/unassigned/`
- `/api/incidents/by-status/`

**Note:** Use query params instead: `?my_incidents=true` or `?status=UNASSIGNED`

---

### 5️⃣ SURVEILLANCE (`/api/surveillance/`)

#### ✅ POST `/api/surveillance/ingest/`
```javascript
// Body
{
  "camera_id": 1,
  "event_type": "string",
  "frame_url": "string",
  "ai_data": {
    "confidence": 0.95,
    "bounding_boxes": [[100, 200, 400, 500]],
    "detected_objects": ["string"]
  }
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/surveillance/events/`
- `/api/surveillance/events/{id}/`
- `/api/surveillance/events/by-camera/`
- `/api/surveillance/events/by-type/`
- `/api/surveillance/events/by-date/`

---

### 6️⃣ TRACKING (`/api/tracking/`)

#### ✅ POST `/api/tracking/ingest/`
```javascript
// Body
{
  "camera_id": 1,
  "vector": [0.123, 0.456, 0.789],
  "person_id": "string"
}
```

#### ✅ GET `/api/tracking/`
**Query params:**
- `?person_id=PERSON_xyz`
- `?camera_id=1`
- `?time_window=60`

#### ❌ REMOVED (Not in official schema):
- `/api/tracking/records/`
- `/api/tracking/person/{personId}/path/`
- `/api/tracking/by-camera/`
- `/api/tracking/stats/`

**Note:** Use base endpoint with query params instead

---

### 7️⃣ NOTIFICATIONS (`/api/mobile/`)

#### ✅ POST `/api/mobile/send-sms/`
```javascript
// Body
{
  "phone_number": "+1234567890",
  "message": "string"
}
```

#### ✅ POST `/api/mobile/send-email/`
```javascript
// Body
{
  "email_address": "string",
  "subject": "string",
  "message": "string"
}
```

#### ✅ POST `/api/mobile/send-bulk/`
```javascript
// Body
{
  "user_ids": [1, 2],
  "subject": "string",
  "message": "string",
  "send_sms": true,
  "send_email": true
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/mobile/history/`
- `/api/mobile/templates/`

---

### 8️⃣ DASHBOARD (`/api/dashboard/`)

#### 🔧 CORRECTED: GET `/api/dashboard/`
**Changed from:** Multiple sub-endpoints → **Single unified endpoint**
```javascript
// Query params
?days=30
?limit=20
```

#### ❌ REMOVED (Not in official schema):
- `/api/dashboard/overview/`
- `/api/dashboard/alert-stats/`
- `/api/dashboard/incident-stats/`
- `/api/dashboard/camera-stats/`
- `/api/dashboard/recent-activity/`
- `/api/dashboard/system-health/`

**Note:** All dashboard data now comes from the single `/api/dashboard/` endpoint

---

### 9️⃣ FEEDBACK (`/api/feedback/`)

#### ✅ POST `/api/feedback/`
```javascript
// Body
{
  "type": "GENERAL" | "INCIDENT" | "FALSE_POSITIVE" | "TRUE_POSITIVE",
  "message": "string"
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/feedback/my-feedback/`
- `/api/feedback/stats/`
- `/api/feedback/by-user/`

---

### 🔟 PERSONNEL (`/api/personnel/`)

#### ✅ GET `/api/personnel/`
**Query params:**
- `?zone=Zone_A`

#### ✅ POST `/api/personnel/`
```javascript
// Body
{
  "user": 1,
  "phone": "+1234567890",
  "assigned_zones": ["Zone A", "Zone B"]
}
```

#### ❌ REMOVED (Not in official schema):
- `/api/personnel/my-profile/`
- `/api/personnel/by-role/`
- `/api/personnel/available-guards/`

---

## 🔑 Key Changes Summary

### Field Name Changes:
| Old Field | New Field | Endpoint |
|-----------|-----------|----------|
| `guard_id` | `assigned_to` | `/api/incidents/{id}/assign/` |
| `resolution` | `notes` | `/api/incidents/{id}/status/` |

### Method Changes:
| Endpoint | Old Method | New Method |
|----------|------------|------------|
| `/api/alerts/{id}/acknowledge/` | POST | **PATCH** |
| `/api/incidents/{id}/assign/` | POST | **PATCH** |

### Removed Endpoints:
Total **25+ endpoints** removed that were not in the official schema.

### Query Param Corrections:
- Cameras: Use `?zone=Zone_A` and `?status=ONLINE`
- Alerts: Use `?status=ACTIVE&camera_id=1&alert_type=...&severity=HIGH`
- Incidents: Use `?status=ASSIGNED&assigned_to=2&my_incidents=true`
- Tracking: Use `?person_id=...&camera_id=...&time_window=60`
- Personnel: Use `?zone=Zone_A`
- Dashboard: Use `?days=30&limit=20`

---

## 🚀 How to Use Corrected APIs

### Example: Creating an Alert
```javascript
import { createAlert } from './api/alerts';

const alertData = {
  camera_id: 1,
  alert_type: "intrusion_detected",
  severity: "HIGH",
  metadata: {
    confidence: 0.95,
    frame_url: "https://example.com/frame.jpg"
  }
};

const response = await createAlert(alertData);
```

### Example: Acknowledging an Alert
```javascript
import { acknowledgeAlert } from './api/alerts';

// ✅ CORRECT (PATCH with status in body)
await acknowledgeAlert(alertId, "ACKED");
```

### Example: Assigning an Incident
```javascript
import { assignIncident } from './api/incidents';

// ✅ CORRECT (assigned_to instead of guard_id)
await assignIncident(incidentId, userId, "Investigating the issue");
```

### Example: Updating Incident Status
```javascript
import { updateIncidentStatus } from './api/incidents';

// ✅ CORRECT (notes instead of resolution)
await updateIncidentStatus(incidentId, "RESOLVED", "Issue resolved successfully");
```

### Example: Filtering Cameras
```javascript
import { listCameras } from './api/cameras';

// ✅ CORRECT (using query params)
const onlineCameras = await listCameras({ status: "ONLINE", zone: "Zone_A" });
```

---

## ⚠️ Breaking Changes for Frontend Components

Components using the following APIs need to be updated:

1. **Alert components** - Update acknowledge calls to use PATCH with status parameter
2. **Incident components** - Update assign calls to use `assigned_to` instead of `guard_id`
3. **Incident components** - Update status calls to use `notes` instead of `resolution`
4. **Camera components** - Remove calls to `/active/` and `/by-zone/` endpoints
5. **Dashboard components** - Update to use single `/api/dashboard/` endpoint with query params
6. **Tracking components** - Use base endpoint with query params instead of sub-endpoints

---

## ✅ Validation Checklist

- [x] All POST/PATCH/PUT body parameters match schema
- [x] All HTTP methods are correct
- [x] All query parameters documented
- [x] Authorization headers configured in axios interceptor
- [x] No extra endpoints that don't exist in backend
- [x] Field names match exactly (assigned_to, notes, etc.)
- [x] Enum values documented (ONLINE/OFFLINE, HIGH/MEDIUM/LOW, etc.)

---

## 📝 Notes

1. **Authorization**: The axios interceptor automatically adds `Authorization: Bearer <token>` to all requests
2. **Content-Type**: All requests use `Content-Type: application/json`
3. **Token Refresh**: Automatically handled by axios interceptor on 401 responses
4. **Error Handling**: All 400 errors should now be resolved with these corrections

---

**Last Updated:** 2025-11-23
**Status:** ✅ All APIs Corrected

