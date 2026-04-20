# ✅ FIXED: Registration 400 Bad Request

## 🎯 Root Cause

The frontend was sending fields that the backend doesn't accept:
- ❌ `first_name` (not in backend schema)
- ❌ `last_name` (not in backend schema)

According to the official API schema, registration only accepts:
```javascript
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password2": "string",
  "role": "ADMIN | SECURITY_INCHARGE | GUARD"
}
```

---

## 🔧 What Was Fixed

### 1. Removed Unsupported Fields
**Before:**
```javascript
const [formData, setFormData] = useState({
  username: '',
  email: '',
  password: '',
  password2: '',
  first_name: '',    // ❌ Not in backend schema
  last_name: '',     // ❌ Not in backend schema
  role: 'GUARD',
});
```

**After:**
```javascript
const [formData, setFormData] = useState({
  username: '',
  email: '',
  password: '',
  password2: '',
  role: 'GUARD',
});
```

### 2. Removed Form Fields
Removed the `first_name` and `last_name` input fields from the registration form.

### 3. Added Better Error Logging
Added comprehensive error logging to help diagnose future issues:
```javascript
console.log('📤 [Register] Sending registration data:', formData);
console.error('❌ [Register] Error response:', error.response?.data);
```

### 4. Improved Error Messages
Now shows specific field errors:
- Username errors
- Email errors
- Password errors
- Role errors
- General validation errors

---

## 🚀 Test Registration Now

### Step 1: Refresh Browser
Press `Ctrl + Shift + R`

### Step 2: Go to Registration Page
Navigate to `/register`

### Step 3: Fill Out Form
You'll now see a simpler form with only:
- ✅ Username
- ✅ Email
- ✅ Role (dropdown)
- ✅ Password
- ✅ Confirm Password

### Step 4: Submit
Click "Register" button

### Expected Result:
- ✅ Success toast: "Registration successful! Please login."
- ✅ Redirects to login page
- ✅ No 400 errors!

---

## 🔍 If Still Getting Errors

### Check Browser Console
Open F12 → Console tab and look for:
```
📤 [Register] Sending registration data: {...}
❌ [Register] Error response: {...}
```

### Common Validation Errors:

#### 1. Username Already Exists
```
Error: "Username: A user with that username already exists."
```
**Solution:** Use a different username

#### 2. Email Already Exists
```
Error: "Email: User with this email already exists."
```
**Solution:** Use a different email

#### 3. Password Too Short
```
Error: "Password: This password is too short."
```
**Solution:** Use a longer password (usually 8+ characters)

#### 4. Passwords Don't Match
```
Error: "Password confirmation: The two password fields didn't match."
```
**Solution:** Make sure both password fields match

#### 5. Invalid Role
```
Error: "Role: Invalid role."
```
**Solution:** Use one of: ADMIN, SECURITY_INCHARGE, GUARD

---

## 📋 Correct Registration Request

### Request Format:
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john_guard",
  "email": "john@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123",
  "role": "GUARD"
}
```

### Response (Success):
```json
{
  "user": {
    "id": 1,
    "username": "john_guard",
    "email": "john@example.com",
    "role": "GUARD",
    ...
  },
  "message": "User registered successfully"
}
```

---

## ✅ Summary

**Problem:** Frontend sending `first_name` and `last_name` fields not in backend schema
**Solution:** Removed unsupported fields from form and state
**Status:** ✅ **FIXED!**

---

## 📝 Notes

If your backend DOES support `first_name` and `last_name` in the future, you can add them back. But according to the API schema you provided, they're not currently supported in the registration endpoint.

The user model might have these fields, but the `UserCreateSerializer` doesn't accept them during registration. They might need to be added via profile update after registration.

---

**Registration should now work without 400 errors!** 🎉

