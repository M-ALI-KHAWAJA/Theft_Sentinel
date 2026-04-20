# API Endpoint Fixes - Dashboard & Feedback

## 🐛 Issues Fixed

### Issue 1: Dashboard 404 Errors
**Problem**: Frontend was calling `/api/dashboard/` but backend had no root endpoint.

**Root Cause**: The `dashboard.js` file had all API functions pointing to the same `/api/dashboard/` endpoint instead of their specific paths.

**Solution**: Updated frontend API calls to use correct specific endpoints.

---

### Issue 2: Feedback Primary Key Type Mismatch
**Problem**: Feedback URLs used `<int:pk>` but MongoDB uses ObjectId (string type).

**Root Cause**: URL patterns were configured for integer primary keys, incompatible with MongoDB's ObjectId.

**Solution**: Changed URL patterns from `<int:pk>` to `<str:pk>`.

---

## 📋 Changes Made

### Frontend: `src/api/dashboard.js`

#### Before (Incorrect ❌)
```javascript
export const getDashboardOverview = (params = {}) => {
  return axiosInstance.get('/api/dashboard/', { params });
};

export const getAlertStats = (params = {}) => {
  return axiosInstance.get('/api/dashboard/', { params });
};
// ... all pointing to same endpoint
```

#### After (Correct ✅)
```javascript
export const getDashboardOverview = (params = {}) => {
  return axiosInstance.get('/api/dashboard/overview/', { params });
};

export const getAlertStats = (params = {}) => {
  return axiosInstance.get('/api/dashboard/alerts-stats/', { params });
};

export const getIncidentStats = (params = {}) => {
  return axiosInstance.get('/api/dashboard/incidents-stats/', { params });
};

export const getCameraStats = (params = {}) => {
  return axiosInstance.get('/api/dashboard/cameras-stats/', { params });
};

export const getRecentActivity = (params = {}) => {
  return axiosInstance.get('/api/dashboard/recent-activity/', { params });
};
```

---

### Backend: `apps/feedback/urls.py`

#### Before (Incorrect ❌)
```python
urlpatterns = [
    path('', FeedbackListCreateView.as_view(), name='feedback_list_create'),
    path('<int:pk>/', FeedbackDetailView.as_view(), name='feedback_detail'),
    path('<int:pk>/delete/', FeedbackDeleteView.as_view(), name='feedback_delete'),
    # ...
]
```

#### After (Correct ✅)
```python
urlpatterns = [
    path('', FeedbackListCreateView.as_view(), name='feedback_list_create'),
    path('<str:pk>/', FeedbackDetailView.as_view(), name='feedback_detail'),
    path('<str:pk>/delete/', FeedbackDeleteView.as_view(), name='feedback_delete'),
    # ...
]
```

---

## 🔍 Complete Dashboard API Reference

### Available Endpoints

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/dashboard/overview/` | GET | Overall dashboard statistics | Admin, In-Charge |
| `/api/dashboard/alerts-stats/` | GET | Detailed alert statistics | Admin, In-Charge |
| `/api/dashboard/incidents-stats/` | GET | Detailed incident statistics | Admin, In-Charge |
| `/api/dashboard/cameras-stats/` | GET | Camera statistics | Admin, In-Charge |
| `/api/dashboard/recent-activity/` | GET | Recent activity feed | Admin, In-Charge |

### Query Parameters

All dashboard endpoints support optional query parameters:
- `days` (integer): Number of days for historical data (default: 30)
- `limit` (integer): Limit for recent activity (default: 20)

### Example Requests

#### Get Dashboard Overview
```bash
GET /api/dashboard/overview/
GET /api/dashboard/overview/?days=7
```

#### Get Alert Statistics
```bash
GET /api/dashboard/alerts-stats/
GET /api/dashboard/alerts-stats/?days=30
```

#### Get Recent Activity
```bash
GET /api/dashboard/recent-activity/
GET /api/dashboard/recent-activity/?limit=50
```

---

## 🔍 Complete Feedback API Reference

### Available Endpoints

| Endpoint | Method | Description | Permissions |
|----------|--------|-------------|-------------|
| `/api/feedback/` | GET | List all feedback | Admin (all), Others (own) |
| `/api/feedback/` | POST | Create new feedback | All authenticated |
| `/api/feedback/<id>/` | GET | Get feedback by ID | Admin (all), Others (own) |
| `/api/feedback/<id>/` | PUT | Update feedback | Admin (all), Others (own) |
| `/api/feedback/<id>/` | DELETE | Delete feedback | Admin only |
| `/api/feedback/<id>/delete/` | DELETE | Delete feedback (alt) | Admin only |
| `/api/feedback/me/` | GET | Get my feedback | All authenticated |
| `/api/feedback/stats/` | GET | Feedback statistics | Admin only |

### Example Requests

#### List Feedback
```bash
GET /api/feedback/
GET /api/feedback/?type=FALSE_POSITIVE
```

#### Create Feedback
```bash
POST /api/feedback/
Content-Type: application/json

{
  "type": "FALSE_POSITIVE",
  "message": "This alert was incorrect"
}
```

#### Get Specific Feedback
```bash
GET /api/feedback/507f1f77bcf86cd799439011/
```

#### Delete Feedback (Admin)
```bash
DELETE /api/feedback/507f1f77bcf86cd799439011/delete/
```

---

## ✅ Verification

### Dashboard Endpoints
```bash
# Test overview
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/dashboard/overview/

# Test alert stats
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/dashboard/alerts-stats/?days=7

# Test recent activity
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/dashboard/recent-activity/?limit=10
```

### Feedback Endpoints
```bash
# List feedback
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/feedback/

# Create feedback
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"type": "GENERAL", "message": "Test feedback"}' \
  http://localhost:8000/api/feedback/

# Get specific feedback (use actual ObjectId)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/feedback/507f1f77bcf86cd799439011/
```

---

## 🔧 MongoDB ObjectId Notes

### Why `<str:pk>` instead of `<int:pk>`?

MongoDB uses ObjectId for primary keys, which are 24-character hexadecimal strings (e.g., `507f1f77bcf86cd799439011`), not integers.

### Affected Models
All models using `ObjectIdAutoField` need `<str:pk>` in URLs:
- ✅ Feedback
- ✅ User (accounts)
- ✅ Camera
- ✅ Alert
- ✅ Incident
- ✅ Personnel
- ✅ And all other models

### URL Pattern Check
```python
# ❌ Wrong for MongoDB
path('<int:pk>/', MyView.as_view())

# ✅ Correct for MongoDB
path('<str:pk>/', MyView.as_view())
```

---

## 📝 Testing Checklist

- [x] Dashboard overview loads without 404
- [x] Alert statistics load correctly
- [x] Incident statistics load correctly
- [x] Camera statistics load correctly
- [x] Recent activity loads correctly
- [x] Feedback list loads without errors
- [x] Feedback creation works
- [x] Feedback detail view works with ObjectId
- [x] Feedback deletion works (admin only)
- [x] Django system check passes
- [x] No linter errors

---

## 🚀 Status

✅ **All dashboard endpoints fixed**  
✅ **All feedback endpoints fixed**  
✅ **MongoDB ObjectId compatibility ensured**  
✅ **Django system check passed**  
✅ **No breaking changes**  

---

**Last Updated**: November 24, 2025  
**Issues Fixed**: Dashboard 404, Feedback ObjectId mismatch  
**Status**: Production Ready ✅

