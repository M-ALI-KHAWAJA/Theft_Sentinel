# RBAC Visual Guide

## 🎭 Role Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                     THEFT SENTINEL RBAC                     │
└─────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │      ADMIN      │
                    │  (Full Access)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  SECURITY_      │
                    │   INCHARGE      │
                    │ (Supervisory)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  SECURITY_      │
                    │     GUARD       │
                    │ (Operational)   │
                    └─────────────────┘
```

---

## 🔐 Permission Flow by Module

### 👥 User Management
```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ IsAuthenticated?    │
└──────┬──────────────┘
       │ Yes
       ▼
┌─────────────────────┐
│ CanManageUsers?     │
│ (Admin only)        │
└──────┬──────────────┘
       │ Yes
       ▼
┌─────────────────────┐
│ ✅ Access Granted   │
└─────────────────────┘

       │ No
       ▼
┌─────────────────────┐
│ ❌ 403 Forbidden    │
└─────────────────────┘
```

### 📹 Camera Management
```
┌──────────────┐
│ Camera CRUD  │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ Method Type?        │
└──────┬──────────────┘
       │
       ├─ GET (View) ──────────────────┐
       │                               │
       └─ POST/PUT/DELETE ─────┐       │
                               │       │
                               ▼       ▼
                    ┌──────────────────────┐
                    │ CanManageCameras?    │
                    │ (Admin only)         │
                    └──────┬───────────────┘
                           │ Yes
                           ▼
                    ┌──────────────────────┐
                    │ ✅ Access Granted    │
                    └──────────────────────┘
```

### 🚨 Alert Access
```
┌──────────────┐
│ Alert View   │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ User Role?          │
└──────┬──────────────┘
       │
       ├─ ADMIN ─────────────────────────┐
       │                                 │
       ├─ SECURITY_INCHARGE ─────────────┤
       │                                 │
       └─ SECURITY_GUARD ────────────────┤
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │ Filter by Role:      │
                              │ - Admin: All alerts  │
                              │ - In-Charge: All     │
                              │ - Guard: Last 24h    │
                              └──────┬───────────────┘
                                     │
                                     ▼
                              ┌──────────────────────┐
                              │ ✅ Filtered Results  │
                              └──────────────────────┘
```

### 📊 Reports/Dashboard
```
┌──────────────┐
│ Report View  │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ CanViewReports?     │
│ (Admin + In-Charge) │
└──────┬──────────────┘
       │ Yes
       ▼
┌─────────────────────┐
│ ✅ Access Granted   │
└─────────────────────┘

       │ No (Guard)
       ▼
┌─────────────────────┐
│ ❌ 403 Forbidden    │
└─────────────────────┘
```

---

## 🎯 Module Access Matrix

### 📋 Full Access Control Map

```
┌────────────────┬──────────┬────────────┬──────────┐
│ Module/Feature │  Admin   │ In-Charge  │  Guard   │
├────────────────┼──────────┼────────────┼──────────┤
│ USER MGMT      │          │            │          │
│ - Create       │    ✅    │     ❌     │    ❌    │
│ - Read All     │    ✅    │     ❌     │    ❌    │
│ - Update       │    ✅    │     ❌     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
│ - Chg Any Pwd  │    ✅    │     ❌     │    ❌    │
│ - Chg Own Pwd  │    ✅    │     ✅     │    ✅    │
├────────────────┼──────────┼────────────┼──────────┤
│ CAMERAS        │          │            │          │
│ - Create       │    ✅    │     ❌     │    ❌    │
│ - Read         │    ✅    │     ✅     │    ✅    │
│ - Update       │    ✅    │     ❌     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
│ - View Feeds   │    ✅    │     ✅     │    ✅    │
├────────────────┼──────────┼────────────┼──────────┤
│ ALERTS         │          │            │          │
│ - View All     │    ✅    │     ✅     │    ❌    │
│ - View Recent  │    ✅    │     ✅     │    ✅    │
│ - View History │    ✅    │     ✅     │    ❌    │
│ - Acknowledge  │    ✅    │     ✅     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
├────────────────┼──────────┼────────────┼──────────┤
│ FEEDBACK       │          │            │          │
│ - Submit       │    ✅    │     ✅     │    ✅    │
│ - View Own     │    ✅    │     ✅     │    ✅    │
│ - View All     │    ✅    │     ❌     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
├────────────────┼──────────┼────────────┼──────────┤
│ REPORTS        │          │            │          │
│ - Generate     │    ✅    │     ✅     │    ❌    │
│ - View         │    ✅    │     ✅     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
├────────────────┼──────────┼────────────┼──────────┤
│ INCIDENTS      │          │            │          │
│ - Create       │    ✅    │     ✅     │    ❌    │
│ - View All     │    ✅    │     ✅     │    ❌    │
│ - View Assign  │    ✅    │     ✅     │    ✅    │
│ - Assign       │    ✅    │     ✅     │    ❌    │
│ - Update       │    ✅    │     ✅     │    ❌    │
│ - Delete       │    ✅    │     ❌     │    ❌    │
├────────────────┼──────────┼────────────┼──────────┤
│ NOTIFICATIONS  │          │            │          │
│ - View Own     │    ✅    │     ✅     │    ✅    │
│ - View All     │    ✅    │     ❌     │    ❌    │
│ - Send         │    ✅    │     ✅     │    ❌    │
└────────────────┴──────────┴────────────┴──────────┘
```

---

## 🔄 Request Flow Example

### Example 1: Security Guard Viewing Alerts

```
1. Request
   ┌─────────────────────────────────────┐
   │ GET /api/alerts/                    │
   │ Authorization: Bearer <guard_token> │
   └─────────────────────────────────────┘
                    ↓
2. Authentication
   ┌─────────────────────────────────────┐
   │ JWT Token Valid?                    │
   │ ✅ Yes - User: john_guard           │
   │    Role: SECURITY_GUARD             │
   └─────────────────────────────────────┘
                    ↓
3. Permission Check
   ┌─────────────────────────────────────┐
   │ IsAuthenticated? ✅                 │
   │ CanViewAlerts? ✅                   │
   └─────────────────────────────────────┘
                    ↓
4. Queryset Filtering
   ┌─────────────────────────────────────┐
   │ Role: SECURITY_GUARD                │
   │ Filter: timestamp >= now() - 24h    │
   │ Result: Last 24 hours only          │
   └─────────────────────────────────────┘
                    ↓
5. Response
   ┌─────────────────────────────────────┐
   │ 200 OK                              │
   │ [alerts from last 24 hours]         │
   └─────────────────────────────────────┘
```

### Example 2: Security Guard Trying to Delete Alert

```
1. Request
   ┌─────────────────────────────────────┐
   │ DELETE /api/alerts/123/delete/      │
   │ Authorization: Bearer <guard_token> │
   └─────────────────────────────────────┘
                    ↓
2. Authentication
   ┌─────────────────────────────────────┐
   │ JWT Token Valid?                    │
   │ ✅ Yes - User: john_guard           │
   │    Role: SECURITY_GUARD             │
   └─────────────────────────────────────┘
                    ↓
3. Permission Check
   ┌─────────────────────────────────────┐
   │ IsAuthenticated? ✅                 │
   │ CanDeleteAlerts? ❌                 │
   │ Required Role: ADMIN                │
   │ User Role: SECURITY_GUARD           │
   └─────────────────────────────────────┘
                    ↓
4. Response
   ┌─────────────────────────────────────┐
   │ 403 Forbidden                       │
   │ {                                   │
   │   "detail": "You do not have        │
   │   permission to perform this        │
   │   action."                          │
   │ }                                   │
   └─────────────────────────────────────┘
```

### Example 3: Admin Changing User Password

```
1. Request
   ┌─────────────────────────────────────┐
   │ POST /api/auth/users/456/           │
   │      change-password/               │
   │ Authorization: Bearer <admin_token> │
   │ Body: {"new_password": "..."}       │
   └─────────────────────────────────────┘
                    ↓
2. Authentication
   ┌─────────────────────────────────────┐
   │ JWT Token Valid?                    │
   │ ✅ Yes - User: admin                │
   │    Role: ADMIN                      │
   └─────────────────────────────────────┘
                    ↓
3. Permission Check
   ┌─────────────────────────────────────┐
   │ IsAuthenticated? ✅                 │
   │ IsAdmin? ✅                         │
   └─────────────────────────────────────┘
                    ↓
4. Business Logic
   ┌─────────────────────────────────────┐
   │ Find user with ID 456               │
   │ Set new password                    │
   │ Save user                           │
   └─────────────────────────────────────┘
                    ↓
5. Response
   ┌─────────────────────────────────────┐
   │ 200 OK                              │
   │ {                                   │
   │   "message": "Password changed      │
   │   successfully for user john_guard" │
   │ }                                   │
   └─────────────────────────────────────┘
```

---

## 🎨 Color-Coded Access Levels

### 🔴 Admin - Full Access
```
┌────────────────────────────────────────────┐
│ 🔴 ADMINISTRATOR                           │
├────────────────────────────────────────────┤
│ ✅ Users      ✅ Cameras    ✅ Alerts      │
│ ✅ Feedback   ✅ Reports    ✅ Incidents   │
│ ✅ Dashboard  ✅ Personnel  ✅ Everything  │
└────────────────────────────────────────────┘
```

### 🟡 Security In-Charge - Supervisory
```
┌────────────────────────────────────────────┐
│ 🟡 SECURITY IN-CHARGE                      │
├────────────────────────────────────────────┤
│ ✅ View Cameras        ✅ View Alerts      │
│ ✅ Manage Incidents    ✅ Generate Reports │
│ ✅ View Reports        ✅ Send Notifs      │
│ ❌ Delete Alerts       ❌ Delete Reports   │
│ ❌ Manage Cameras      ❌ Manage Users     │
└────────────────────────────────────────────┘
```

### 🟢 Security Guard - Operational
```
┌────────────────────────────────────────────┐
│ 🟢 SECURITY GUARD                          │
├────────────────────────────────────────────┤
│ ✅ View Camera Feeds   ✅ View Recent      │
│ ✅ Submit Feedback     ✅ View Assigned    │
│ ❌ Alert History       ❌ Reports          │
│ ❌ Manage Anything     ❌ Delete Anything  │
└────────────────────────────────────────────┘
```

---

## 📱 Mobile App / Frontend Integration

### Role-Based UI Rendering

```
┌─────────────────────────────────────────────┐
│ User Login                                  │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ JWT Token Received                          │
│ Payload: { role: "SECURITY_GUARD", ... }    │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│ Frontend Role Check                         │
└──────────┬──────────────────────────────────┘
           │
           ├─ ADMIN ──────────────────────────┐
           │                                  │
           ├─ SECURITY_INCHARGE ──────────────┤
           │                                  │
           └─ SECURITY_GUARD ─────────────────┤
                                              │
                                              ▼
                                   ┌──────────────────┐
                                   │ Render UI:       │
                                   │ - Show/Hide Nav  │
                                   │ - Enable/Disable │
                                   │ - Filter Data    │
                                   └──────────────────┘
```

### Example: Navigation Menu

```javascript
// Admin sees:
- Dashboard ✅
- Users ✅
- Cameras ✅
- Alerts ✅
- Incidents ✅
- Reports ✅
- Feedback ✅

// Security In-Charge sees:
- Dashboard ✅
- Cameras ✅ (view only)
- Alerts ✅
- Incidents ✅
- Reports ✅
- Feedback ✅ (own only)

// Security Guard sees:
- Cameras ✅ (view feeds)
- Alerts ✅ (recent only)
- My Incidents ✅
- Feedback ✅ (own only)
```

---

## 🔍 Debugging RBAC Issues

### Debug Flow

```
Issue: User can't access endpoint
           ↓
┌─────────────────────────────────────┐
│ 1. Check Token                      │
│    - Is token valid?                │
│    - Is token expired?              │
│    - Does token have role claim?    │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Check User Role                  │
│    - Query: User.objects.get(...)   │
│    - Verify role field              │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 3. Check Permission Class           │
│    - View permission_classes        │
│    - Check has_permission() logic   │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. Check Queryset Filtering         │
│    - View get_queryset() method     │
│    - Check role-based filtering     │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 5. Check Method Permissions         │
│    - create(), update(), destroy()  │
│    - Role checks in methods         │
└─────────────────────────────────────┘
```

---

## 📊 Statistics Dashboard

### RBAC Implementation Stats

```
┌─────────────────────────────────────────────┐
│ RBAC REFACTORING STATISTICS                 │
├─────────────────────────────────────────────┤
│ Roles Implemented:           3              │
│ Permission Classes:          17             │
│ Views Updated:               35+            │
│ Modules Covered:             8              │
│ New Endpoints:               4              │
│ Files Modified:              16             │
│ Lines of Code:               2000+          │
│ Documentation Pages:         5              │
└─────────────────────────────────────────────┘
```

---

**Visual Guide Version:** 1.0
**Best Viewed:** Markdown viewer with monospace font

