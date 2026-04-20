# RBAC Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Review
- [x] All RBAC changes implemented
- [x] No linting errors
- [x] Permission classes created
- [x] Views updated with RBAC logic
- [x] Documentation completed

### ✅ Files Modified (16 files)
- [x] `apps/accounts/models.py`
- [x] `apps/accounts/permissions.py`
- [x] `apps/accounts/views.py`
- [x] `apps/accounts/urls.py`
- [x] `apps/cameras/views.py`
- [x] `apps/alerts/views.py`
- [x] `apps/alerts/urls.py`
- [x] `apps/feedback/views.py`
- [x] `apps/feedback/urls.py`
- [x] `apps/incidents/views.py`
- [x] `apps/mobile/views.py`
- [x] `apps/dashboard/views.py`
- [x] `apps/personnel/views.py`
- [x] `RBAC_REFACTORING.md`
- [x] `RBAC_MIGRATION_SCRIPT.py`
- [x] `RBAC_SUMMARY.md`

---

## Deployment Steps

### Step 1: Backup Database
```bash
# MongoDB backup
mongodump --uri="mongodb://localhost:27017/theft_sentinel" --out=/backup/pre-rbac-migration

# Or use your backup method
```

### Step 2: Deploy Code
```bash
# Pull latest code
git pull origin main

# Or deploy via your CI/CD pipeline
```

### Step 3: Run Migration Script
```bash
# Option 1: Direct execution
python manage.py shell < RBAC_MIGRATION_SCRIPT.py

# Option 2: Interactive
python manage.py shell
>>> exec(open('RBAC_MIGRATION_SCRIPT.py').read())
```

**Expected Output:**
```
============================================================
RBAC Role Migration Script
============================================================

📊 Found X user(s) with 'GUARD' role

🔄 Migrating roles...

✅ Successfully migrated X user(s)
   GUARD → SECURITY_GUARD

📊 Current role distribution:
   - ADMIN: X
   - SECURITY_INCHARGE: X
   - SECURITY_GUARD: X
   - GUARD (old): 0

✅ Migration completed successfully!
============================================================
```

### Step 4: Verify Migration
```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Should be 0
print("Old GUARD users:", User.objects.filter(role='GUARD').count())

# Should show migrated users
print("New SECURITY_GUARD users:", User.objects.filter(role='SECURITY_GUARD').count())

# Check all roles
print("\nRole distribution:")
print("ADMIN:", User.objects.filter(role='ADMIN').count())
print("SECURITY_INCHARGE:", User.objects.filter(role='SECURITY_INCHARGE').count())
print("SECURITY_GUARD:", User.objects.filter(role='SECURITY_GUARD').count())
```

### Step 5: Restart Application
```bash
# Restart Django/Gunicorn
sudo systemctl restart gunicorn

# Or your restart method
```

### Step 6: Verify API Endpoints
```bash
# Test authentication
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Test with each role
# Save the token and test endpoints
```

---

## Post-Deployment Testing

### Test Admin Role
```bash
# Get token
TOKEN="<admin_token>"

# Test user management (should work)
curl -X GET http://localhost:8000/api/auth/users/ \
  -H "Authorization: Bearer $TOKEN"

# Test camera management (should work)
curl -X POST http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Camera", "location": "Test", "zone": "A", "rtsp_url": "rtsp://test"}'

# Test alert deletion (should work)
curl -X DELETE http://localhost:8000/api/alerts/1/delete/ \
  -H "Authorization: Bearer $TOKEN"

# Test feedback deletion (should work)
curl -X DELETE http://localhost:8000/api/feedback/1/delete/ \
  -H "Authorization: Bearer $TOKEN"

# Test dashboard access (should work)
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test Security In-Charge Role
```bash
# Get token
TOKEN="<incharge_token>"

# Test user management (should fail)
curl -X GET http://localhost:8000/api/auth/users/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: 403 Forbidden

# Test camera management (should fail for POST)
curl -X POST http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Camera", "location": "Test", "zone": "A", "rtsp_url": "rtsp://test"}'
# Expected: 403 Forbidden

# Test viewing cameras (should work)
curl -X GET http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer $TOKEN"

# Test viewing alerts (should work)
curl -X GET http://localhost:8000/api/alerts/ \
  -H "Authorization: Bearer $TOKEN"

# Test alert deletion (should fail)
curl -X DELETE http://localhost:8000/api/alerts/1/delete/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: 403 Forbidden

# Test dashboard access (should work)
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test Security Guard Role
```bash
# Get token
TOKEN="<guard_token>"

# Test viewing alerts (should work - last 24 hours only)
curl -X GET http://localhost:8000/api/alerts/ \
  -H "Authorization: Bearer $TOKEN"

# Test viewing camera feeds (should work)
curl -X GET http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer $TOKEN"

# Test submitting feedback (should work)
curl -X POST http://localhost:8000/api/feedback/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "TRUE_POSITIVE", "notes": "Test feedback"}'

# Test dashboard access (should fail)
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer $TOKEN"
# Expected: 403 Forbidden

# Test creating incidents (should fail)
curl -X POST http://localhost:8000/api/incidents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"alert_id": 1, "notes": "Test"}'
# Expected: 403 Forbidden
```

---

## Frontend Updates (If Needed)

### Update Role Checks
```javascript
// OLD CODE
if (user.role === 'GUARD') {
  // Guard-specific logic
}

// NEW CODE
if (user.role === 'SECURITY_GUARD') {
  // Security Guard-specific logic
}
```

### Update Role Constants
```javascript
// constants.js or similar
export const USER_ROLES = {
  ADMIN: 'ADMIN',
  SECURITY_INCHARGE: 'SECURITY_INCHARGE',
  SECURITY_GUARD: 'SECURITY_GUARD', // Changed from GUARD
};
```

### Update UI Components
```javascript
// Check all components that display or check roles
// Search for: 'GUARD'
// Replace with: 'SECURITY_GUARD'

// Common files to check:
// - src/store/authSlice.js
// - src/components/ProtectedRoute.jsx
// - src/pages/Dashboard.jsx
// - src/layouts/MainLayout.jsx
```

---

## Rollback Plan (If Needed)

### If Migration Fails
```bash
# Restore from backup
mongorestore --uri="mongodb://localhost:27017/theft_sentinel" /backup/pre-rbac-migration

# Revert code
git revert <commit_hash>

# Restart application
sudo systemctl restart gunicorn
```

### If Issues Found Post-Deployment
```bash
# Revert migration
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Revert SECURITY_GUARD back to GUARD
User.objects.filter(role='SECURITY_GUARD').update(role='GUARD')
```

---

## Monitoring

### Check Logs
```bash
# Application logs
tail -f /var/log/gunicorn/error.log

# Django logs
tail -f /var/log/django/django.log

# Look for permission errors
grep "403" /var/log/gunicorn/access.log
grep "permission" /var/log/django/django.log
```

### Monitor Errors
- Check for 403 Forbidden errors
- Verify users can access appropriate endpoints
- Monitor authentication failures

---

## Success Criteria

### ✅ Migration Success
- [ ] No GUARD users remaining
- [ ] All users migrated to SECURITY_GUARD
- [ ] No errors in migration script output

### ✅ Application Health
- [ ] Application starts without errors
- [ ] Authentication works for all roles
- [ ] API endpoints respond correctly

### ✅ RBAC Enforcement
- [ ] Admin can access all endpoints
- [ ] Security In-Charge has correct permissions
- [ ] Security Guard has correct restrictions
- [ ] Permission errors return 403 with clear messages

### ✅ Frontend Compatibility
- [ ] Frontend can authenticate
- [ ] Role-based UI rendering works
- [ ] No JavaScript errors related to roles

---

## Contact & Support

### Documentation
- **Full Details:** `RBAC_REFACTORING.md`
- **Summary:** `RBAC_SUMMARY.md`
- **This Checklist:** `RBAC_DEPLOYMENT_CHECKLIST.md`

### Key Files
- **Permission Classes:** `apps/accounts/permissions.py`
- **User Model:** `apps/accounts/models.py`
- **Migration Script:** `RBAC_MIGRATION_SCRIPT.py`

### Testing
- Test each role thoroughly
- Verify all permission restrictions
- Check error messages are user-friendly

---

## Final Notes

### ⚠️ Important
- This is a **one-time migration**
- Backup database before deployment
- Test in staging environment first
- Have rollback plan ready

### ✅ What Changed
- Role enum: `GUARD` → `SECURITY_GUARD`
- Permission system completely refactored
- RBAC enforced across all modules

### ✅ What Didn't Change
- API endpoint URLs
- Request/response structures
- Database schema (except role enum)
- Authentication mechanism
- Business logic (except permissions)

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Status:** _____________
**Issues:** _____________

