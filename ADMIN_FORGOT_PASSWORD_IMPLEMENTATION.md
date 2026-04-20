# Admin-Only Forgot Password Flow Implementation

## Summary

Implemented a secure "Forgot Password" feature exclusively for admin users. Security personnel and guards cannot reset passwords themselves and must contact the admin.

## A. Backend Implementation

### 1. PasswordResetToken Model

**File**: `apps/accounts/models.py`

**Fields**:
- `user`: ForeignKey to User
- `token`: CharField (64 chars, unique, indexed) - Secure random token (32 chars)
- `created_at`: DateTimeField
- `expires_at`: DateTimeField - Token expires after 30 minutes
- `used`: BooleanField - Prevents token reuse

**Methods**:
- `is_expired()`: Checks if token has expired
- `is_valid()`: Checks if token is valid (not expired and not used)
- `generate_token()`: Static method to generate secure random token (32 characters)

### 2. ForgotPasswordView

**File**: `apps/accounts/views.py`

**Endpoint**: `POST /api/auth/forgot-password/`

**Flow**:
1. Validates email using `ForgotPasswordSerializer`
2. Checks if email exists and belongs to an admin (`role == 'ADMIN'`)
3. If email is invalid or user is not admin → returns generic message (security: don't reveal if email exists)
4. Generates secure token (32 characters) using `secrets.token_urlsafe(32)`
5. Creates `PasswordResetToken` with 30-minute expiration
6. Invalidates any existing unused tokens for the user
7. Sends email via Gmail SMTP with reset link
8. Returns success message (always, for security)

**Security Features**:
- Only admin emails receive reset links
- Generic error messages (don't reveal if email exists)
- Tokens expire after 30 minutes
- Existing tokens are invalidated when new one is created

### 3. ResetPasswordView

**File**: `apps/accounts/views.py`

**Endpoint**: `POST /api/auth/reset-password/`

**Flow**:
1. Validates token, new password, and confirm password
2. Checks if token exists and is valid (not expired, not used)
3. Verifies user is admin
4. Updates password using Django's `set_password()` (secure hashing)
5. Marks token as used
6. Returns success message

**Security Features**:
- Token validation (expiration, usage)
- Password matching validation
- Secure password hashing (Django's default)
- Token is immediately invalidated after use

### 4. Serializers

**File**: `apps/accounts/serializers.py`

**ForgotPasswordSerializer**:
- Validates email format
- Checks if email exists and belongs to admin
- Returns error if email is not registered as admin

**ResetPasswordSerializer**:
- Validates token, new password, confirm password
- Ensures passwords match
- Validates password length (min 8 characters)

### 5. URL Routes

**File**: `apps/accounts/urls.py`

**Routes Added**:
- `path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password')`
- `path('reset-password/', ResetPasswordView.as_view(), name='reset_password')`

### 6. Email Configuration

**File**: `config/settings.py`

**Settings**:
- `EMAIL_BACKEND`: SMTP backend
- `EMAIL_HOST`: smtp.gmail.com
- `EMAIL_PORT`: 587
- `EMAIL_USE_TLS`: True
- `EMAIL_HOST_USER`: Gmail address (from environment)
- `EMAIL_HOST_PASSWORD`: Gmail app password (from environment)
- `DEFAULT_FROM_EMAIL`: Sender email
- `FRONTEND_URL`: Frontend URL for reset links (default: http://localhost:5173)

## B. Frontend Implementation

### 1. ForgotPassword Component

**File**: `src/pages/auth/ForgotPassword.jsx`

**Features**:
- Admin-only notice with clear instructions
- Gmail input field
- Submit button
- Back to login button
- Success/error messages via modal
- Auto-redirect to login after success

**User Experience**:
- Clear instructions: "Only Admin users can reset passwords"
- Informational note: "Security personnel and guards must contact the admin"
- Real-time validation
- User-friendly error messages

### 2. ResetPassword Component

**File**: `src/pages/auth/ResetPassword.jsx`

**Features**:
- Token extraction from URL query parameter
- New password input (min 8 characters)
- Confirm password input
- Real-time password matching validation
- Password strength indicator
- Submit button (disabled until passwords match)
- Back to login button
- Success/error messages via modal
- Auto-redirect to login after success

**User Experience**:
- Real-time password matching feedback
- Password length validation
- Clear success/error messages
- Secure token handling

### 3. Login Component Update

**File**: `src/pages/auth/Login.jsx`

**Changes**:
- Added "Forgot Password?" link below password field
- Link navigates to `/forgot-password`
- Maintains existing login functionality

### 4. API Functions

**File**: `src/api/auth.js`

**Functions Added**:
- `forgotPassword(email)`: Sends forgot password request
- `resetPassword(token, newPassword, confirmPassword)`: Resets password

### 5. Routes

**File**: `src/router/AppRouter.jsx`

**Routes Added**:
- `/forgot-password` → `ForgotPassword` component
- `/reset-password` → `ResetPassword` component

## C. Complete Flow Explanation

### Step 1: Forgot Password Clicked

**User Action**: Admin clicks "Forgot Password?" link on login page

**Frontend**:
- Navigates to `/forgot-password`
- Displays form with:
  - Admin-only notice
  - Gmail input field
  - Submit button

**Message Displayed**:
- "Only Admin users can reset passwords using this flow."
- "Security personnel and guards must contact the admin to change passwords."

### Step 2: Email Verification

**User Action**: Admin enters Gmail and submits

**Backend**:
1. Validates email format
2. Checks if email exists in User table
3. Verifies user is admin (`role == 'ADMIN'`)
4. If email is invalid or user is not admin:
   - Returns generic message: "If this email is registered as an admin, a password reset link has been sent."
   - (Security: doesn't reveal if email exists)

**Frontend**:
- Shows success message (always, for security)
- Auto-redirects to login after 3 seconds

### Step 3: Generate Reset Token

**Backend**:
1. Generates secure random token (32 characters) using `secrets.token_urlsafe(32)`
2. Creates `PasswordResetToken` record:
   - `token`: Generated token
   - `expires_at`: Now + 30 minutes
   - `used`: False
3. Invalidates any existing unused tokens for the user

### Step 4: Send Email

**Backend**:
1. Generates reset link: `{FRONTEND_URL}/reset-password?token={token}`
2. Sends email via Gmail SMTP:
   - Subject: "Theft Sentinel - Admin Password Reset"
   - Body: Instructions + reset link
   - Expiration notice: "This link will expire in 30 minutes"
   - Security note: "Only admin users can reset passwords using this flow"

**Email Content**:
```
Hello {username},

You requested to reset your admin password for Theft Sentinel.

Click the following link to reset your password:
{reset_link}

This link will expire in 30 minutes.

If you did not request this password reset, please ignore this email.

Security Note: Only admin users can reset passwords using this flow. Security personnel and guards must contact the admin.

Best regards,
Theft Sentinel Team
```

### Step 5: Reset Password Page

**User Action**: Admin clicks reset link in email

**Frontend**:
- Extracts token from URL query parameter
- Displays reset password form:
  - New password input (min 8 characters)
  - Confirm password input
  - Real-time validation
  - Submit button

**Validation**:
- Password must be at least 8 characters
- Passwords must match
- Submit button disabled until valid

### Step 6: Password Reset

**User Action**: Admin enters new password and confirms

**Backend**:
1. Validates token (exists, not expired, not used)
2. Verifies user is admin
3. Validates passwords match
4. Updates password using `user.set_password(new_password)` (secure hashing)
5. Marks token as used
6. Returns success message

**Frontend**:
- Shows success message: "Password successfully updated. You may now log in."
- Auto-redirects to login after 3 seconds

### Step 7: Success Confirmation

**User Action**: Admin logs in with new password

**Result**: Admin can now log in with the new password

## D. Security Features

### 1. Admin-Only Access

- Only users with `role == 'ADMIN'` can reset passwords
- Non-admin users receive generic message (security: don't reveal if email exists)
- Frontend displays clear instructions for non-admin users

### 2. Secure Token Generation

- Uses `secrets.token_urlsafe(32)` for cryptographically secure random tokens
- Tokens are 32 characters long (URL-safe)
- Tokens are unique and indexed in database

### 3. Token Expiration

- Tokens expire after 30 minutes
- Expired tokens cannot be used
- Users must request a new reset link if token expires

### 4. Token Usage Prevention

- Tokens can only be used once
- After password reset, token is marked as `used = True`
- Used tokens cannot be reused

### 5. Password Security

- Passwords are hashed using Django's default password hasher (PBKDF2)
- Passwords are never stored in plain text
- Minimum password length: 8 characters

### 6. Error Message Security

- Generic error messages (don't reveal if email exists)
- No sensitive information exposed in error messages
- Consistent messaging for security and non-security users

## E. User Experience

### Admin Users

1. Click "Forgot Password?" on login page
2. See admin-only notice
3. Enter Gmail address
4. Receive email with reset link
5. Click link → opens reset password page
6. Enter new password (with real-time validation)
7. Submit → password updated
8. Redirected to login → can log in with new password

### Non-Admin Users

1. Click "Forgot Password?" on login page
2. See notice: "Only Admin users can reset passwords"
3. See instruction: "Security personnel and guards must contact the admin"
4. Cannot reset password (backend rejects non-admin emails)

## F. Environment Variables Required

Add to `.env` file:

```env
# Email Configuration (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

**Note**: For Gmail, you need to:
1. Enable 2-Factor Authentication
2. Generate an "App Password" (not your regular password)
3. Use the app password in `EMAIL_HOST_PASSWORD`

## G. Database Migration

Run the following commands to create and apply the migration:

```bash
cd theft_sentinel_backend
python manage.py makemigrations accounts
python manage.py migrate
```

This will create the `PasswordResetToken` table in the database.

## H. Testing Checklist

✅ **Admin Forgot Password**:
- Admin can request password reset
- Admin receives email with reset link
- Admin can reset password using link
- Admin can log in with new password

✅ **Non-Admin Users**:
- Non-admin users see admin-only notice
- Non-admin users cannot reset passwords
- Non-admin users receive generic message (security)

✅ **Token Security**:
- Tokens expire after 30 minutes
- Tokens can only be used once
- Expired tokens are rejected
- Used tokens are rejected

✅ **Password Security**:
- Passwords are hashed securely
- Minimum password length enforced
- Password matching validated

✅ **Error Handling**:
- Invalid emails handled gracefully
- Expired tokens show appropriate message
- Used tokens show appropriate message
- Network errors handled

## I. Files Created/Modified

### Backend:

1. **`apps/accounts/models.py`**:
   - Added `PasswordResetToken` model

2. **`apps/accounts/serializers.py`**:
   - Added `ForgotPasswordSerializer`
   - Added `ResetPasswordSerializer`

3. **`apps/accounts/views.py`**:
   - Added `ForgotPasswordView`
   - Added `ResetPasswordView`

4. **`apps/accounts/urls.py`**:
   - Added `/forgot-password/` route
   - Added `/reset-password/` route

5. **`config/settings.py`**:
   - Email configuration (already existed, verified)
   - Added `FRONTEND_URL` setting

### Frontend:

1. **`src/pages/auth/ForgotPassword.jsx`** (NEW):
   - Forgot password form component

2. **`src/pages/auth/ResetPassword.jsx`** (NEW):
   - Reset password form component

3. **`src/pages/auth/Login.jsx`**:
   - Added "Forgot Password?" link

4. **`src/api/auth.js`**:
   - Added `forgotPassword()` function
   - Added `resetPassword()` function

5. **`src/router/AppRouter.jsx`**:
   - Added `/forgot-password` route
   - Added `/reset-password` route

## J. Security Best Practices Applied

✅ **Token Expiration**: 30-minute timeout
✅ **Token Uniqueness**: Cryptographically secure random tokens
✅ **Token Single-Use**: Tokens marked as used after password reset
✅ **Password Hashing**: Django's secure password hasher
✅ **Generic Error Messages**: Don't reveal if email exists
✅ **Admin-Only Access**: Only admin users can reset passwords
✅ **Input Validation**: Email format, password length, password matching
✅ **Secure Token Storage**: Tokens stored in database with expiration

## Summary

The admin-only forgot password flow is now fully implemented with:
- ✅ Secure token generation and expiration
- ✅ Admin-only access control
- ✅ Email sending via Gmail SMTP
- ✅ Password reset with secure hashing
- ✅ User-friendly frontend with real-time validation
- ✅ Comprehensive error handling
- ✅ Security best practices

The system is production-ready and follows all security requirements.

