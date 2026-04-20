# RBAC Quick Reference Guide

## 🎯 Three Roles, Three Access Levels

### 🔴 ADMIN (Administrator)
**Full System Access**
- ✅ Everything

### 🟡 SECURITY_INCHARGE (Security In-Charge)
**Supervisory Access**
- ✅ View & manage alerts (cannot delete)
- ✅ Generate & view reports (cannot delete)
- ✅ Manage incidents
- ✅ Send notifications
- ❌ No camera management
- ❌ No user management

### 🟢 SECURITY_GUARD (Security Guard)
**Operational Access**
- ✅ View camera feeds
- ✅ View recent alerts (24h only)
- ✅ Submit feedback
- ✅ View assigned incidents
- ❌ No alert history
- ❌ No reports/dashboard
- ❌ No management capabilities

---

## 📊 Permission Matrix (Quick View)

| Feature | Admin | In-Charge | Guard |
|---------|:-----:|:---------:|:-----:|
| **Users** |
| Manage users | ✅ | ❌ | ❌ |
| Change any password | ✅ | ❌ | ❌ |
| Change own password | ✅ | ✅ | ✅ |
| **Cameras** |
| Manage cameras | ✅ | ❌ | ❌ |
| View feeds | ✅ | ✅ | ✅ |
| **Alerts** |
| View all alerts | ✅ | ✅ | 24h only |
| Delete alerts | ✅ | ❌ | ❌ |
| Acknowledge | ✅ | ✅ | ❌ |
| **Feedback** |
| Submit | ✅ | ✅ | ✅ |
| View all | ✅ | ❌ | ❌ |
| Delete | ✅ | ❌ | ❌ |
| **Reports** |
| Generate | ✅ | ✅ | ❌ |
| View | ✅ | ✅ | ❌ |
| Delete | ✅ | ❌ | ❌ |
| **Incidents** |
| Create | ✅ | ✅ | ❌ |
| View all | ✅ | ✅ | ❌ |
| View assigned | ✅ | ✅ | ✅ |
| Assign | ✅ | ✅ | ❌ |
| Delete | ✅ | ❌ | ❌ |

---

## 🔑 Key Restrictions by Role

### Security Guard Restrictions
1. **Alert History:** Can only view alerts from last 24 hours
2. **Reports:** Cannot access dashboard or reports
3. **Management:** Cannot create, update, or delete anything
4. **Visibility:** Can only see data assigned to them or their own submissions

### Security In-Charge Restrictions
1. **Deletion:** Cannot delete alerts, reports, or feedback
2. **Cameras:** Cannot add, edit, or delete cameras
3. **Users:** Cannot manage user accounts
4. **Passwords:** Can only change their own password

---

## 🚀 Quick Deployment

### 1. Deploy Code
```bash
git pull origin main
```

### 2. Migrate Roles
```bash
python manage.py shell < RBAC_MIGRATION_SCRIPT.py
```

### 3. Verify
```bash
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(role='GUARD').count()  # Should be 0
```

### 4. Restart
```bash
sudo systemctl restart gunicorn
```

---

## 🧪 Quick Test Commands

### Test Admin
```bash
# Should work - Admin can do everything
curl -X DELETE http://localhost:8000/api/alerts/1/delete/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Test Security In-Charge
```bash
# Should fail - Cannot delete alerts
curl -X DELETE http://localhost:8000/api/alerts/1/delete/ \
  -H "Authorization: Bearer $INCHARGE_TOKEN"

# Should work - Can view reports
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer $INCHARGE_TOKEN"
```

### Test Security Guard
```bash
# Should fail - Cannot access dashboard
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer $GUARD_TOKEN"

# Should work - Can view recent alerts
curl -X GET http://localhost:8000/api/alerts/recent/ \
  -H "Authorization: Bearer $GUARD_TOKEN"
```

---

## 📝 Common Error Messages

### 403 Forbidden Responses

**User Management:**
```json
{
  "error": "You do not have permission to create users. Only Admin can manage users."
}
```

**Camera Management:**
```json
{
  "error": "You do not have permission to add cameras. Only Admin can manage cameras."
}
```

**Alert Deletion:**
```json
{
  "error": "You do not have permission to delete alerts. Only Admin can delete alerts."
}
```

**Report Access:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Incident Creation:**
```json
{
  "error": "You do not have permission to create incidents."
}
```

---

## 🔍 Troubleshooting

### Issue: User can't access expected endpoint
**Check:**
1. User's role: `User.objects.get(username='user').role`
2. Token is valid and not expired
3. Permission class on the view
4. Queryset filtering in get_queryset()

### Issue: Migration didn't work
**Solution:**
```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Manual migration
User.objects.filter(role='GUARD').update(role='SECURITY_GUARD')
```

### Issue: Frontend shows wrong role
**Check:**
1. Token payload: Decode JWT token
2. User serializer includes role
3. Frontend is using 'SECURITY_GUARD' not 'GUARD'

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `RBAC_REFACTORING.md` | Complete technical documentation |
| `RBAC_SUMMARY.md` | Executive summary |
| `RBAC_DEPLOYMENT_CHECKLIST.md` | Step-by-step deployment |
| `RBAC_QUICK_REFERENCE.md` | This file - quick lookup |
| `RBAC_MIGRATION_SCRIPT.py` | Database migration script |

---

## 🎯 Remember

### ✅ Changed
- Role enum: `GUARD` → `SECURITY_GUARD`
- Permission system refactored
- Granular access control implemented

### ✅ Unchanged
- API endpoint URLs
- Request/response structures
- Authentication mechanism
- Business logic (except permissions)

### ⚠️ Action Required
- Run migration script once
- Update frontend role checks
- Test all three roles thoroughly

---

## 📞 Need Help?

1. **Full Details:** See `RBAC_REFACTORING.md`
2. **Permission Classes:** Check `apps/accounts/permissions.py`
3. **View Logic:** Check individual view files in each app
4. **Migration:** Run `RBAC_MIGRATION_SCRIPT.py`

---

**Quick Reference Version:** 1.0
**Last Updated:** 2025-01-24

