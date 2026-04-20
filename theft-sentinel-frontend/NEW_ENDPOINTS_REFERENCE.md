# 🔗 New Endpoints Integration Reference

## Quick Reference for New Backend Endpoints

---

## 1️⃣ User Detail (Admin Only)

### Endpoint
```
GET/PUT/PATCH/DELETE /api/auth/users/<user_id>/
```

### Frontend Integration

#### Get User
```javascript
import { getUser } from '../../api/auth';

const response = await getUser(userId);
console.log(response.data); // { id, username, email, role, is_active, ... }
```

#### Update User (Full)
```javascript
import { updateUser } from '../../api/auth';

const data = {
  username: 'john_doe',
  email: 'john@example.com',
  role: 'GUARD',
  is_active: true
};

await updateUser(userId, data);
```

#### Update User (Partial)
```javascript
import { patchUser } from '../../api/auth';

const data = {
  role: 'SECURITY_INCHARGE'  // Only update role
};

await patchUser(userId, data);
```

#### Delete User
```javascript
import { deleteUser } from '../../api/auth';

await deleteUser(userId);
```

### Usage in UI
- **File:** `src/pages/personnel/List.jsx`
- **File:** `src/pages/personnel/Edit.jsx`

---

## 2️⃣ Admin Change User Password

### Endpoint
```
POST /api/auth/users/<user_id>/change-password/
```

### Request Body
```json
{
  "new_password": "newSecurePassword123"
}
```

### Frontend Integration

```javascript
import { adminChangeUserPassword } from '../../api/auth';

const data = {
  new_password: 'newSecurePassword123'
};

await adminChangeUserPassword(userId, data);
```

### Validation
- ✅ Minimum 8 characters
- ✅ Password confirmation match
- ✅ Admin only

### Usage in UI
- **File:** `src/pages/personnel/Edit.jsx`
- **Component:** Password Change Modal
- **Trigger:** "Change Password" button

---

## 3️⃣ Delete Alert (Admin Only)

### Endpoint
```
DELETE /api/alerts/<alert_id>/delete/
```

### Frontend Integration

```javascript
import { adminDeleteAlert } from '../../api/alerts';

await adminDeleteAlert(alertId);
```

### Usage in UI
- **File:** `src/pages/alerts/List.jsx`
- **Component:** `AlertCard` with delete button
- **Visibility:** Admin only
- **Confirmation:** Yes (window.confirm)

---

## 4️⃣ Delete Feedback (Admin Only)

### Endpoint
```
DELETE /api/feedback/<feedback_id>/delete/
```

### Frontend Integration

```javascript
import { adminDeleteFeedback } from '../../api/feedback';

await adminDeleteFeedback(feedbackId);
```

### Usage in UI
- **File:** `src/pages/feedback/List.jsx`
- **Component:** Delete button in table actions
- **Visibility:** Admin only
- **Confirmation:** Yes (window.confirm)

---

## 🎨 Centered Modal Usage

All new endpoints use the centered modal system for success/error messages.

### Import
```javascript
import CenteredModal from '../../components/CenteredModal';
import { useModal } from '../../hooks/useModal';
```

### Setup
```javascript
const { modalState, showSuccess, showError, hideModal } = useModal();
```

### Display Modal in JSX
```jsx
<CenteredModal
  show={modalState.show}
  type={modalState.type}
  message={modalState.message}
  onClose={hideModal}
/>
```

### Show Messages
```javascript
// Success
showSuccess('User updated successfully');

// Error
showError('Failed to update user');

// Warning
showWarning('This action cannot be undone');

// Info
showInfo('Please wait...');
```

---

## 🔒 Role-Based Access Control

All new endpoints are **Admin Only**.

### Check User Role
```javascript
import { useRecoilValue } from 'recoil';
import { authUserState } from '../../store/authStore';

const user = useRecoilValue(authUserState);
const isAdmin = user?.role === 'ADMIN';
```

### Conditional Rendering
```jsx
{isAdmin && (
  <button onClick={handleDelete}>Delete</button>
)}
```

---

## 📋 Complete API Reference

### Auth API (`src/api/auth.js`)
```javascript
// Existing
login(credentials)
logout()
getProfile()
updateProfile(data)
changePassword(data)
listUsers(params)

// New/Updated
getUser(id)                          // ✨ Enhanced
updateUser(id, data)                 // ✨ Enhanced
patchUser(id, data)                  // ✨ NEW
deleteUser(id)                       // ✨ Enhanced
adminChangeUserPassword(userId, data) // ✨ NEW
```

### Alerts API (`src/api/alerts.js`)
```javascript
// Existing
listAlerts(params)
getAlert(id)
createAlert(data)
updateAlert(id, data)
patchAlert(id, data)
deleteAlert(id)
acknowledgeAlert(id, status)

// New
adminDeleteAlert(id)                 // ✨ NEW
```

### Feedback API (`src/api/feedback.js`)
```javascript
// Existing
listFeedback(params)
getFeedback(id)
createFeedback(data)
updateFeedback(id, data)
deleteFeedback(id)

// New
adminDeleteFeedback(id)              // ✨ NEW
```

---

## 🧪 Testing Guide

### Test User Management
1. Login as admin
2. Go to Personnel (User Management)
3. Click "View/Edit" on a user
4. Update user details → Check centered success message
5. Click "Change Password" → Enter new password → Check success message
6. Go back to list → Click "Delete" → Confirm → Check success message

### Test Alert Delete
1. Login as admin
2. Go to Alerts
3. Find an alert card
4. Click "Delete Alert" button
5. Confirm deletion
6. Check centered success message

### Test Feedback Delete
1. Login as admin
2. Go to Feedback
3. Find a feedback row
4. Click "Delete" button
5. Confirm deletion
6. Check centered success message

---

## 🐛 Error Handling

All endpoints include comprehensive error handling:

```javascript
try {
  await someAPICall();
  showSuccess('Operation successful');
} catch (error) {
  console.error('Error:', error);
  const errorMsg = error.response?.data?.detail || 
                   error.response?.data?.error || 
                   'Operation failed';
  showError(errorMsg);
}
```

### Common Error Responses
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Not logged in
- `403 Forbidden` - Not admin
- `404 Not Found` - Resource doesn't exist
- `500 Server Error` - Backend issue

---

## 📚 Related Files

### Components
- `src/components/CenteredModal.jsx` - Modal component
- `src/components/AlertCard.jsx` - Alert card with delete

### Hooks
- `src/hooks/useModal.js` - Modal state management

### API Services
- `src/api/auth.js` - User management
- `src/api/alerts.js` - Alert operations
- `src/api/feedback.js` - Feedback operations

### Pages
- `src/pages/personnel/List.jsx` - User list
- `src/pages/personnel/Edit.jsx` - User edit + password change
- `src/pages/alerts/List.jsx` - Alerts with delete
- `src/pages/feedback/List.jsx` - Feedback with delete

---

**Last Updated:** November 24, 2025  
**Version:** 1.0.0

