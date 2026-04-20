# Migration Guide: Updating Frontend Code

This guide helps you update existing frontend components to use the corrected API calls.

## 🔄 Required Code Changes

### 1. Alerts - Acknowledge Method

#### ❌ OLD CODE
```javascript
// Wrong: Using POST without status parameter
const handleAcknowledge = async (alertId) => {
  await acknowledgeAlert(alertId);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Using PATCH with status parameter
const handleAcknowledge = async (alertId, status = "ACKED") => {
  await acknowledgeAlert(alertId, status);
};
```

---

### 2. Incidents - Assign Method

#### ❌ OLD CODE
```javascript
// Wrong: Using guard_id field
const handleAssign = async (incidentId, guardId) => {
  await axiosInstance.post(`/api/incidents/${incidentId}/assign/`, {
    guard_id: guardId
  });
};
```

#### ✅ NEW CODE
```javascript
// Correct: Using assigned_to field with PATCH
import { assignIncident } from './api/incidents';

const handleAssign = async (incidentId, userId, notes = '') => {
  await assignIncident(incidentId, userId, notes);
};
```

---

### 3. Incidents - Update Status

#### ❌ OLD CODE
```javascript
// Wrong: Using resolution field
const handleResolve = async (incidentId, resolutionText) => {
  await updateIncidentStatus(incidentId, "RESOLVED", resolutionText);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Using notes field (parameter name is the same, just different backend field)
const handleResolve = async (incidentId, notes) => {
  await updateIncidentStatus(incidentId, "RESOLVED", notes);
};
```

---

### 4. Cameras - Active Cameras

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getActiveCameras } from './api/cameras';

const fetchActiveCameras = async () => {
  const response = await getActiveCameras();
  setCameras(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listCameras with status query param
import { listCameras } from './api/cameras';

const fetchActiveCameras = async () => {
  const response = await listCameras({ status: "ONLINE" });
  setCameras(response.data);
};
```

---

### 5. Cameras - By Zone

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getCamerasByZone } from './api/cameras';

const fetchZoneCameras = async (zone) => {
  const response = await getCamerasByZone(zone);
  setCameras(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listCameras with zone query param
import { listCameras } from './api/cameras';

const fetchZoneCameras = async (zone) => {
  const response = await listCameras({ zone });
  setCameras(response.data);
};
```

---

### 6. Alerts - Active Alerts

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getActiveAlerts } from './api/alerts';

const fetchActiveAlerts = async () => {
  const response = await getActiveAlerts();
  setAlerts(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listAlerts with status query param
import { listAlerts } from './api/alerts';

const fetchActiveAlerts = async () => {
  const response = await listAlerts({ status: "ACTIVE" });
  setAlerts(response.data);
};
```

---

### 7. Alerts - By Severity

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getAlertsBySeverity } from './api/alerts';

const fetchHighSeverityAlerts = async () => {
  const response = await getAlertsBySeverity("HIGH");
  setAlerts(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listAlerts with severity query param
import { listAlerts } from './api/alerts';

const fetchHighSeverityAlerts = async () => {
  const response = await listAlerts({ severity: "HIGH" });
  setAlerts(response.data);
};
```

---

### 8. Incidents - My Incidents

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getMyIncidents } from './api/incidents';

const fetchMyIncidents = async () => {
  const response = await getMyIncidents();
  setIncidents(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listIncidents with my_incidents query param
import { listIncidents } from './api/incidents';

const fetchMyIncidents = async () => {
  const response = await listIncidents({ my_incidents: true });
  setIncidents(response.data);
};
```

---

### 9. Incidents - By Status

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getIncidentsByStatus } from './api/incidents';

const fetchUnassignedIncidents = async () => {
  const response = await getIncidentsByStatus("UNASSIGNED");
  setIncidents(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listIncidents with status query param
import { listIncidents } from './api/incidents';

const fetchUnassignedIncidents = async () => {
  const response = await listIncidents({ status: "UNASSIGNED" });
  setIncidents(response.data);
};
```

---

### 10. Dashboard - Specific Stats

#### ❌ OLD CODE
```javascript
// Wrong: Multiple separate endpoints
import { 
  getDashboardOverview, 
  getAlertStats, 
  getCameraStats 
} from './api/dashboard';

const fetchDashboardData = async () => {
  const overview = await getDashboardOverview();
  const alerts = await getAlertStats({ days: 30 });
  const cameras = await getCameraStats();
};
```

#### ✅ NEW CODE
```javascript
// Correct: Single endpoint with query params
import { getDashboardOverview } from './api/dashboard';

const fetchDashboardData = async () => {
  const response = await getDashboardOverview({ days: 30, limit: 20 });
  // All data comes from single response
};
```

---

### 11. Tracking - Person Path

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getPersonPath } from './api/tracking';

const fetchPersonPath = async (personId) => {
  const response = await getPersonPath(personId);
  setPath(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listTrackingRecords with person_id query param
import { listTrackingRecords } from './api/tracking';

const fetchPersonPath = async (personId) => {
  const response = await listTrackingRecords({ person_id: personId });
  setPath(response.data);
};
```

---

### 12. Personnel - Available Guards

#### ❌ OLD CODE
```javascript
// Wrong: Non-existent endpoint
import { getAvailableGuards } from './api/personnel';

const fetchGuards = async () => {
  const response = await getAvailableGuards();
  setGuards(response.data);
};
```

#### ✅ NEW CODE
```javascript
// Correct: Use listPersonnel (filtering should be done on backend or client-side)
import { listPersonnel } from './api/personnel';

const fetchGuards = async () => {
  const response = await listPersonnel();
  // Filter for guards if needed
  const guards = response.data.filter(p => p.role === 'GUARD');
  setGuards(guards);
};
```

---

## 📝 Component Update Checklist

Go through each component and check:

- [ ] **Alert components**
  - [ ] Update `acknowledgeAlert()` calls to include status parameter
  - [ ] Replace `getActiveAlerts()` with `listAlerts({ status: "ACTIVE" })`
  - [ ] Replace `getAlertsBySeverity()` with `listAlerts({ severity: "..." })`

- [ ] **Incident components**
  - [ ] Update `assignIncident()` to use `assigned_to` instead of `guard_id`
  - [ ] Update `updateIncidentStatus()` to use `notes` instead of `resolution`
  - [ ] Replace `getMyIncidents()` with `listIncidents({ my_incidents: true })`
  - [ ] Replace `getIncidentsByStatus()` with `listIncidents({ status: "..." })`

- [ ] **Camera components**
  - [ ] Replace `getActiveCameras()` with `listCameras({ status: "ONLINE" })`
  - [ ] Replace `getCamerasByZone()` with `listCameras({ zone: "..." })`
  - [ ] Remove `updateCameraStatus()` calls (use `patchCamera()` instead)

- [ ] **Dashboard components**
  - [ ] Consolidate dashboard API calls to single `getDashboardOverview()`
  - [ ] Remove separate stats endpoints
  - [ ] Add `days` and `limit` query params

- [ ] **Tracking components**
  - [ ] Replace path endpoints with `listTrackingRecords()` + query params

- [ ] **Personnel components**
  - [ ] Replace role-specific endpoints with `listPersonnel()` + filtering

---

## 🔍 Search & Replace Patterns

Use your IDE's find & replace to quickly update:

### Pattern 1: Acknowledge Alerts
**Find:** `acknowledgeAlert\(([^)]+)\)`
**Replace:** `acknowledgeAlert($1, "ACKED")`

### Pattern 2: Guard ID to Assigned To
**Find:** `guard_id`
**Replace:** `assigned_to`

### Pattern 3: Resolution to Notes
**Find:** `resolution:`
**Replace:** `notes:`

### Pattern 4: Active Cameras
**Find:** `getActiveCameras\(\)`
**Replace:** `listCameras({ status: "ONLINE" })`

---

## 🧪 Testing Your Changes

After updating your code, test:

1. **Alert Acknowledgment**
   - Create an alert
   - Acknowledge it
   - Verify status changes to "ACKED"

2. **Incident Assignment**
   - Create an incident
   - Assign to a user
   - Verify `assigned_to` field is set correctly

3. **Query Parameters**
   - Test camera filtering by zone
   - Test alert filtering by severity
   - Test incident filtering by status

4. **Dashboard**
   - Verify dashboard loads with new endpoint
   - Test different `days` and `limit` params

---

## 🐛 Common Issues & Solutions

### Issue 1: 400 Bad Request on Alert Acknowledgment
**Cause:** Missing status parameter
**Fix:** Always include status: `acknowledgeAlert(id, "ACKED")`

### Issue 2: 400 Bad Request on Incident Assignment
**Cause:** Using `guard_id` instead of `assigned_to`
**Fix:** Use the correct field name in API calls

### Issue 3: 404 Not Found on /active/ or /by-zone/
**Cause:** These endpoints don't exist
**Fix:** Use base endpoint with query params

### Issue 4: Empty Dashboard Response
**Cause:** Wrong endpoint path
**Fix:** Use `/api/dashboard/` instead of `/api/dashboard/overview/`

---

## 📦 Updated Import Statements

Remove these imports (functions removed):
```javascript
// ❌ Remove these
import { 
  getActiveAlerts,
  getRecentAlerts,
  getAlertsBySeverity,
  getActiveCameras,
  getCamerasByZone,
  updateCameraStatus,
  getMyIncidents,
  getUnassignedIncidents,
  getIncidentsByStatus,
  getPersonPath,
  getTrackingByCamera,
  getAvailableGuards,
  getPersonnelByRole
} from './api/...';
```

Keep these imports (functions updated):
```javascript
// ✅ Keep these (but update usage)
import { 
  listAlerts,
  acknowledgeAlert,
  listCameras,
  listIncidents,
  assignIncident,
  updateIncidentStatus,
  listTrackingRecords,
  listPersonnel,
  getDashboardOverview
} from './api/...';
```

---

## 🎯 Priority Order for Updates

1. **HIGH PRIORITY** (Breaking changes):
   - Alert acknowledgment (method + parameter)
   - Incident assignment (field name)
   - Incident status (field name)

2. **MEDIUM PRIORITY** (404 errors):
   - Camera filtering endpoints
   - Alert filtering endpoints
   - Incident filtering endpoints
   - Dashboard endpoints

3. **LOW PRIORITY** (Nice to have):
   - Personnel filtering
   - Tracking endpoints
   - Notification history

---

## ✅ Validation

After migration, verify:

```bash
# No console errors for:
- 400 Bad Request (wrong parameters)
- 404 Not Found (wrong endpoints)
- 401 Unauthorized (missing auth headers)

# All features work:
- Alert creation and acknowledgment
- Incident creation, assignment, and status updates
- Camera listing and filtering
- Dashboard data loading
- Personnel management
```

---

**Need help?** Check `API_CORRECTIONS.md` for full endpoint documentation.

