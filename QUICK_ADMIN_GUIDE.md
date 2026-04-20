# Quick Admin Guide - User Creation

## ⚠️ IMPORTANT: Public Registration is DISABLED

Users can NO LONGER self-register. Only admins can create new user accounts.

---

## 🔑 How to Create New Users

### Method 1: Frontend Admin Panel (Recommended)

1. **Login as Admin**
   - Go to: `http://localhost:3000/login`
   - Use your admin credentials

2. **Navigate to User Management**
   - Look for "Personnel" or "Users" in the admin menu
   - Click "Create New User" or similar button

3. **Fill in User Details**
   - Username
   - Email
   - Password (twice for confirmation)
   - Role (ADMIN, SECURITY_INCHARGE, or GUARD)

4. **Submit**
   - User will be created immediately
   - You'll see a success message

---

### Method 2: API Direct Call

**Endpoint:** `POST /api/auth/register/`

**Requirements:**
- Must be logged in as Admin
- Must include JWT token in Authorization header

**Example:**
```bash
# 1. Login first
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# 2. Copy the "access" token from response

# 3. Create user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_user",
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "role": "GUARD"
  }'
```

---

### Method 3: Django Admin Panel

1. **Access Admin Panel**
   - Go to: `http://localhost:8000/admin/`
   - Login with superuser credentials

2. **Navigate to Users**
   - Click on "Users" in the admin interface

3. **Add User**
   - Click "Add User" button
   - Fill in the form
   - Save

---

## 🛡️ User Roles

### ADMIN
- Full system access
- Can create/edit/delete users
- Can manage all resources
- Can view all reports and analytics

### SECURITY_INCHARGE
- Can view camera feeds
- Can view alerts and history
- Can generate reports
- **Cannot** manage users or cameras

### GUARD
- Can view camera feeds
- Can receive real-time alerts
- Can submit feedback
- **Cannot** view history or manage anything

---

## ❌ What Users CANNOT Do Anymore

- ❌ Self-register through `/register` page (removed)
- ❌ Create accounts without admin approval
- ❌ Access registration API without admin token

---

## 🔒 Security Features

✅ **Authentication Required**: Must be logged in  
✅ **Admin-Only Access**: Only admins can create users  
✅ **Password Validation**: Strong password requirements enforced  
✅ **Email Validation**: Valid email format required  
✅ **Unique Constraints**: No duplicate usernames or emails  

---

## 🆘 Troubleshooting

### "404 Not Found" Error
**Problem**: Frontend can't find the register endpoint  
**Solution**: ✅ FIXED - Endpoint has been re-added with admin protection

### "403 Forbidden" Error
**Problem**: User trying to create account is not an admin  
**Solution**: Only admin users can create new accounts

### "401 Unauthorized" Error
**Problem**: No authentication token or expired token  
**Solution**: Login again to get a fresh token

### Users complaining they can't register
**Problem**: They're looking for the public registration page  
**Solution**: Tell them to contact an administrator for account creation

---

## 📝 Notes for Admins

1. **First Admin Account**: Must be created via Django's `createsuperuser` command:
   ```bash
   python manage.py createsuperuser
   ```

2. **Password Requirements**:
   - Minimum 8 characters
   - Cannot be too common
   - Cannot be entirely numeric
   - Cannot be too similar to username

3. **User Activation**: All created users are active by default. You can deactivate them later if needed.

4. **Bulk User Creation**: If you need to create many users, consider using Django admin's bulk import or create a custom management command.

---

## 📚 Related Documentation

- **Full API Documentation**: `ADMIN_USER_CREATION_API.md`
- **Security Changes**: `REGISTRATION_REMOVAL_SUMMARY.md`
- **Main API Docs**: `API_DOCUMENTATION.md`

---

**Last Updated**: November 24, 2025  
**Status**: Public Registration Disabled ✅  
**Admin Access**: Required for all user creation ✅

