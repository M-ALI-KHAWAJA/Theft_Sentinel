# Quick API Reference Guide

## 🔥 Most Common API Calls

### Authentication
```javascript
import { login, register } from './api/auth';

// Login
await login({ username: "admin", password: "password123" });

// Register
await register({
  username: "newuser",
  email: "user@example.com",
  password: "pass123",
  password2: "pass123",
  role: "GUARD"
});
```

### Cameras
```javascript
import { listCameras, createCamera } from './api/cameras';

// Get all online cameras in Zone A
await listCameras({ zone: "Zone_A", status: "ONLINE" });

// Create camera
await createCamera({
  name: "Front Gate Camera",
  rtsp_url: "rtsp://example.com/stream",
  location: "Main Entrance",
  zone: "Zone_A",
  status: "ONLINE"
});
```

### Alerts
```javascript
import { listAlerts, createAlert, acknowledgeAlert } from './api/alerts';

// Get high severity alerts from camera 1
await listAlerts({ camera_id: 1, severity: "HIGH", status: "ACTIVE" });

// Create alert
await createAlert({
  camera_id: 1,
  alert_type: "intrusion_detected",
  severity: "HIGH",
  metadata: {
    confidence: 0.95,
    frame_url: "https://..."
  }
});

// Acknowledge alert (PATCH method, not POST!)
await acknowledgeAlert(alertId, "ACKED");
```

### Incidents
```javascript
import { listIncidents, createIncident, assignIncident, updateIncidentStatus } from './api/incidents';

// Get my incidents
await listIncidents({ my_incidents: true });

// Create incident
await createIncident({
  alert_id: 1,
  assigned_to: 2,
  notes: "Initial investigation"
});

// Assign incident (use assigned_to, not guard_id!)
await assignIncident(incidentId, userId, "Assigning to senior guard");

// Update status (use notes, not resolution!)
await updateIncidentStatus(incidentId, "RESOLVED", "False alarm confirmed");
```

### Personnel
```javascript
import { listPersonnel, createPersonnel } from './api/personnel';

// Get personnel in Zone A
await listPersonnel({ zone: "Zone_A" });

// Create personnel
await createPersonnel({
  user: 1,
  phone: "+1234567890",
  assigned_zones: ["Zone A", "Zone B"]
});
```

### Dashboard
```javascript
import { getDashboardOverview } from './api/dashboard';

// Get last 30 days data, limit to 20 items
await getDashboardOverview({ days: 30, limit: 20 });
```

### Notifications
```javascript
import { sendSMS, sendEmail, sendBulkNotifications } from './api/mobile';

// Send SMS
await sendSMS({
  phone_number: "+1234567890",
  message: "Alert detected at Zone A"
});

// Send Email
await sendEmail({
  email_address: "guard@example.com",
  subject: "Critical Alert",
  message: "Immediate attention required"
});

// Bulk notifications
await sendBulkNotifications({
  user_ids: [1, 2, 3],
  subject: "System Update",
  message: "Maintenance scheduled",
  send_sms: true,
  send_email: true
});
```

### Feedback
```javascript
import { createFeedback } from './api/feedback';

await createFeedback({
  type: "FALSE_POSITIVE",
  message: "This was not an actual intrusion"
});
```

### Surveillance
```javascript
import { ingestEvent } from './api/surveillance';

await ingestEvent({
  camera_id: 1,
  event_type: "motion_detected",
  frame_url: "https://...",
  ai_data: {
    confidence: 0.95,
    bounding_boxes: [[100, 200, 400, 500]],
    detected_objects: ["person", "vehicle"]
  }
});
```

### Tracking
```javascript
import { ingestTracking, listTrackingRecords } from './api/tracking';

// Ingest tracking data
await ingestTracking({
  camera_id: 1,
  vector: [0.123, 0.456, 0.789],
  person_id: "PERSON_abc123"
});

// Get tracking for specific person
await listTrackingRecords({ person_id: "PERSON_abc123", time_window: 60 });
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ WRONG
```javascript
// Using POST instead of PATCH
await axiosInstance.post(`/api/alerts/${id}/acknowledge/`);

// Wrong field name
await assignIncident(id, { guard_id: 2 });

// Wrong field name
await updateIncidentStatus(id, "RESOLVED", { resolution: "Fixed" });

// Non-existent endpoint
await axiosInstance.get('/api/cameras/active/');
```

### ✅ CORRECT
```javascript
// Use PATCH with status in body
await acknowledgeAlert(id, "ACKED");

// Use assigned_to
await assignIncident(id, 2, "Assigning to guard");

// Use notes
await updateIncidentStatus(id, "RESOLVED", "Fixed");

// Use query params
await listCameras({ status: "ONLINE" });
```

---

## 🎯 Query Parameters Reference

| Endpoint | Available Query Params |
|----------|------------------------|
| `/api/cameras/` | `?zone=Zone_A&status=ONLINE` |
| `/api/alerts/` | `?status=ACTIVE&camera_id=1&alert_type=...&severity=HIGH` |
| `/api/incidents/` | `?status=ASSIGNED&assigned_to=2&my_incidents=true` |
| `/api/tracking/` | `?person_id=PERSON_xyz&camera_id=1&time_window=60` |
| `/api/personnel/` | `?zone=Zone_A` |
| `/api/dashboard/` | `?days=30&limit=20` |

---

## 🔐 Authorization

All authenticated endpoints require:
```javascript
Authorization: Bearer <access_token>
```

This is automatically added by the axios interceptor. Tokens are stored in:
- `localStorage.getItem('access_token')`
- `localStorage.getItem('refresh_token')`

---

## 📊 Enum Values

### Alert Severity
- `HIGH`
- `MEDIUM`
- `LOW`

### Alert/Incident Status
- `ACTIVE`
- `ACKED` (Acknowledged)
- `RESOLVED`

### Incident Workflow Status
- `CREATED`
- `ASSIGNED`
- `ACKNOWLEDGED`
- `RESOLVED`

### Camera Status
- `ONLINE`
- `OFFLINE`

### User Roles
- `ADMIN`
- `SECURITY_INCHARGE`
- `GUARD`

### Feedback Types
- `GENERAL`
- `INCIDENT`
- `FALSE_POSITIVE`
- `TRUE_POSITIVE`

---

## 🔄 Standard CRUD Operations

Most resources follow REST conventions:

```javascript
// List (GET with query params)
await listResource({ param: "value" });

// Get by ID (GET)
await getResource(id);

// Create (POST)
await createResource(data);

// Update (PUT - full update)
await updateResource(id, data);

// Patch (PATCH - partial update)
await patchResource(id, data);

// Delete (DELETE)
await deleteResource(id);
```

