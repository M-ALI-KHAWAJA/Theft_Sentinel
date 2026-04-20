# 🔧 Dashboard 403 Error Fix

## Problem

**Guard users were getting 403 Forbidden errors** when trying to access the dashboard:

```
127.0.0.1:8000/api/dashboard/overview/:1 
Failed to load resource: the server responded with a status of 403 (Forbidden)
```

**Root Cause:**
- Dashboard API endpoints require **Admin or Security In-Charge** permissions
- Guards do NOT have permission to access `/api/dashboard/overview/`
- The router was redirecting ALL users (including Guards) to `/dashboard`
- The dashboard route was not protected, so Guards could access it but couldn't fetch data

---

## Solution

### 1. ✅ Protected Dashboard Route

**Added role-based protection to dashboard route:**

```javascript
<Route
  path="dashboard"
  element={
    <ProtectedRoute allowedRoles={['ADMIN', 'SECURITY_INCHARGE']}>
      <Overview />
    </ProtectedRoute>
  }
/>
```

**Result:** Guards can no longer access `/dashboard` at all.

---

### 2. ✅ Role-Based Home Redirect

**Created smart redirect component:**

```javascript
const RoleBasedRedirect = () => {
  const user = useRecoilValue(authUserState);
  
  if (user?.role === 'GUARD') {
    return <Navigate to="/incidents/my" replace />;
  }
  
  return <Navigate to="/dashboard" replace />;
};
```

**Usage:**
```javascript
<Route index element={<RoleBasedRedirect />} />
```

**Result:**
- Admin → Redirects to `/dashboard`
- Security In-Charge → Redirects to `/dashboard`
- Guard → Redirects to `/incidents/my`

---

### 3. ✅ Updated Protected Route Logic

**Enhanced ProtectedRoute to handle Guards better:**

```javascript
if (allowedRoles && user && !allowedRoles.includes(user.role)) {
  // Redirect based on role
  if (user.role === 'GUARD') {
    return <Navigate to="/incidents/my" replace />;
  }
  return <Navigate to="/dashboard" replace />;
}
```

**Result:** When Guards try to access restricted pages, they're redirected to their incidents page instead of dashboard.

---

## Files Modified

1. **`src/router/AppRouter.jsx`**
   - Added `RoleBasedRedirect` component
   - Protected dashboard route with role check
   - Updated ProtectedRoute logic for Guards

---

## User Flow After Fix

### Admin Login
```
Login → / → /dashboard ✅
```

### Security In-Charge Login
```
Login → / → /dashboard ✅
```

### Guard Login
```
Login → / → /incidents/my ✅
```

---

## Guard's Menu (No Dashboard)

Guards only see:
- My Incidents
- Cameras (view only)
- Feedback
- Logout

**Guards do NOT see Dashboard** in their sidebar menu.

---

## API Permissions Reference

### Dashboard Endpoints (Admin & In-Charge Only)
- `/api/dashboard/overview/` ❌ Guard
- `/api/dashboard/alerts-stats/` ❌ Guard
- `/api/dashboard/incidents-stats/` ❌ Guard
- `/api/dashboard/cameras-stats/` ❌ Guard
- `/api/dashboard/recent-activity/` ❌ Guard

### Guard-Accessible Endpoints
- `/api/incidents/?my_incidents=true` ✅
- `/api/cameras/` ✅
- `/api/cameras/<id>/feed/` ✅
- `/api/feedback/me/` ✅
- `/api/feedback/` (POST) ✅

---

## Testing Checklist

### Admin
- [ ] Login → Lands on Dashboard
- [ ] Dashboard loads data successfully
- [ ] No 403 errors in console

### Security In-Charge
- [ ] Login → Lands on Dashboard
- [ ] Dashboard loads data successfully
- [ ] No 403 errors in console

### Guard
- [ ] Login → Lands on My Incidents page
- [ ] Cannot access `/dashboard` (redirected to My Incidents)
- [ ] No 403 errors in console
- [ ] Can view cameras
- [ ] Can view/submit feedback

---

## Why This Happened

1. **Backend correctly restricts dashboard endpoints** to Admin/In-Charge only
2. **Frontend was not enforcing the same restriction** on the route
3. **All users were redirected to `/dashboard`** regardless of role
4. **Guards could access the page** but got 403 when fetching data

---

## Fix Summary

✅ Dashboard route now protected (Admin & In-Charge only)
✅ Guards redirect to their incidents page on login
✅ Guards redirect to incidents if they try to access dashboard
✅ No more 403 errors for Guards
✅ Each role lands on appropriate home page

---

**Issue Resolved!** Guards will no longer see 403 errors. 🎉

