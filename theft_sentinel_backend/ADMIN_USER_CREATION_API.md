# Admin User Creation API

## 🔒 Security Notice
This endpoint is **ADMIN-ONLY**. Public self-registration has been disabled.

---

## Create New User (Admin Only)

**Endpoint:** `POST /api/auth/register/`

**Authentication Required:** Yes (Admin JWT token)

**Permissions:** 
- `IsAuthenticated` - Must be logged in
- `CanManageUsers` - Must have Admin role

---

### Request Headers
```http
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

### Request Body
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123",
  "password2": "securepass123",
  "role": "GUARD"
}
```

**Field Descriptions:**
- `username` (string, required): Unique username for the new user
- `email` (string, required): Valid email address
- `password` (string, required): Password meeting security requirements
- `password2` (string, required): Password confirmation (must match password)
- `role` (string, required): User role - one of:
  - `"ADMIN"` - Full system access
  - `"SECURITY_INCHARGE"` - Security In-Charge
  - `"GUARD"` - Security Guard

---

### Success Response (201 Created)
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com",
    "role": "GUARD",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  },
  "message": "User created successfully by admin"
}
```

---

### Error Responses

#### 401 Unauthorized (No token provided)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden (Non-admin user)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 400 Bad Request (Validation errors)
```json
{
  "username": ["A user with that username already exists."],
  "email": ["Enter a valid email address."],
  "password": ["This password is too short. It must contain at least 8 characters."],
  "password2": ["Password fields didn't match."]
}
```

---

## Example Usage

### Step 1: Admin Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin_password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

### Step 2: Create New User (with admin token)
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_guard",
    "email": "guard@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "role": "GUARD"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "507f1f77bcf86cd799439012",
    "username": "new_guard",
    "email": "guard@example.com",
    "role": "GUARD",
    "is_active": true,
    "created_at": "2024-01-01T10:30:00Z"
  },
  "message": "User created successfully by admin"
}
```

---

## Frontend Integration

### JavaScript/React Example
```javascript
import { register } from '../../api/auth';

// This function will automatically include the admin's JWT token
// from localStorage via axios interceptors

const createUser = async (userData) => {
  try {
    const response = await register({
      username: userData.username,
      email: userData.email,
      password: userData.password,
      password2: userData.password2,
      role: userData.role
    });
    
    console.log('User created:', response.data.user);
    return response.data;
  } catch (error) {
    if (error.response?.status === 403) {
      console.error('Only admins can create users');
    } else if (error.response?.status === 401) {
      console.error('You must be logged in');
    } else {
      console.error('Validation error:', error.response?.data);
    }
    throw error;
  }
};
```

---

## Security Features

### ✅ What's Protected
1. **Authentication Required**: Must provide valid JWT token
2. **Admin-Only Access**: Only users with `role="ADMIN"` can create users
3. **Password Validation**: Django's built-in password validators enforce security
4. **Email Validation**: Ensures valid email format
5. **Unique Constraints**: Username and email must be unique

### ❌ What's NOT Allowed
1. ❌ Public/anonymous user creation
2. ❌ Self-registration without admin approval
3. ❌ Non-admin users creating other users
4. ❌ Creating users without authentication

---

## Notes

1. **Endpoint Name**: While the endpoint is `/register/`, it's actually an **admin user creation** endpoint, not public registration.

2. **Frontend Route**: The frontend `/register` route has been removed. Admins create users through the admin panel.

3. **Alternative Endpoints**: You can also use:
   - Django Admin Panel: `/admin/`
   - User Management API: `/api/auth/users/` (for listing/updating)

4. **Password Requirements**: Default Django password validators apply:
   - Minimum 8 characters
   - Cannot be too common
   - Cannot be entirely numeric
   - Cannot be too similar to username/email

---

## Troubleshooting

### Issue: 404 Not Found
**Cause**: Endpoint URL is incorrect  
**Solution**: Use `/api/auth/register/` (not `/auth/register/`)

### Issue: 403 Forbidden
**Cause**: User is not an admin  
**Solution**: Only users with `role="ADMIN"` can create users

### Issue: 401 Unauthorized
**Cause**: No JWT token or expired token  
**Solution**: Login first to get a valid token

### Issue: 400 Bad Request
**Cause**: Validation errors (passwords don't match, invalid email, etc.)  
**Solution**: Check the error response for specific field errors

---

## Related Endpoints

- **Login**: `POST /api/auth/login/`
- **List Users**: `GET /api/auth/users/` (Admin only)
- **Get User**: `GET /api/auth/users/<id>/` (Admin only)
- **Update User**: `PUT /api/auth/users/<id>/` (Admin only)
- **Delete User**: `DELETE /api/auth/users/<id>/` (Admin only)
- **Change User Password**: `POST /api/auth/users/<id>/change-password/` (Admin only)

---

**Last Updated**: November 24, 2025  
**API Version**: 1.0  
**Security Level**: Admin-Protected ✅

