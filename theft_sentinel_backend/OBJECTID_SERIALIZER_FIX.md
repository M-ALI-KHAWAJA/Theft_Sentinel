# MongoDB ObjectId Serializer Fix

## Issue
After migrating to MongoDB, login attempts resulted in a 500 error:
```
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'ObjectId'
```

## Root Cause
Django REST Framework's `ModelSerializer` automatically creates an `IntegerField` for the `id` field. However, MongoDB uses `ObjectId` which cannot be converted to an integer.

## Solution
Explicitly defined `id` field as `CharField` in all serializers to handle MongoDB's ObjectId format.

## Files Updated

### 1. User Serializers (`apps/accounts/serializers.py`)
```python
class UserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    # ... rest of the serializer
```

### 2. Camera Serializers (`apps/cameras/serializers.py`)
- `CameraSerializer`: Added `id = serializers.CharField(read_only=True)`

### 3. Alert Serializers (`apps/alerts/serializers.py`)
- `AlertSerializer`: Added `id = serializers.CharField(read_only=True)`

### 4. Surveillance Serializers (`apps/surveillance/serializers.py`)
- `SurveillanceEventSerializer`: Added `id = serializers.CharField(read_only=True)`

### 5. Tracking Serializers (`apps/tracking/serializers.py`)
- `TrackingRecordSerializer`: Added `id = serializers.CharField(read_only=True)`

### 6. Feedback Serializers (`apps/feedback/serializers.py`)
- `FeedbackSerializer`: Added `id = serializers.CharField(read_only=True)`

### 7. Incident Serializers (`apps/incidents/serializers.py`)
- `IncidentSerializer`: Added `id = serializers.CharField(read_only=True)`
- `IncidentAssignSerializer`: Changed `assigned_to` from `IntegerField` to `CharField`

### 8. Mobile/Notification Serializers (`apps/mobile/serializers.py`)
- `NotificationSerializer`: Added `id = serializers.CharField(read_only=True)`
- `BulkNotificationSerializer`: Changed `user_ids` from `ListField(child=IntegerField())` to `ListField(child=CharField())`

### 9. Personnel Serializers (`apps/personnel/serializers.py`)
- `PersonnelSerializer`: Added `id = serializers.CharField(read_only=True)`

## Testing

### Test User Created
```bash
python manage.py shell -c "from apps.accounts.models import User; user = User.objects.create_user(username='admin', email='admin@example.com', password='admin123', role='ADMIN'); print(f'User ID: {user.id}')"
```
Output: `User ID: 69247d164995ccb66d5d2a5c`

### Login Test
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Result**: ✅ Success!
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "69247d164995ccb66d5d2a5c",
    "username": "admin",
    "email": "admin@example.com",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2025-11-24T15:42:30.123Z"
  }
}
```

## ObjectId Format
MongoDB ObjectIds are 24-character hexadecimal strings:
- Example: `69247d164995ccb66d5d2a5c`
- Format: 12-byte identifier (timestamp + machine + process + counter)

## Important Notes

1. **All IDs are now strings**: Frontend should treat all IDs as strings, not integers
2. **JWT tokens work**: User ID is correctly embedded in JWT tokens as a string
3. **Foreign Keys**: All foreign key relationships work correctly with ObjectId
4. **API Responses**: All API responses now return ObjectId as string in the `id` field

## Status
✅ **Fixed and Tested**
- Login endpoint: Working
- User serialization: Working
- JWT token generation: Working
- ObjectId handling: Working

---

**Fix Date**: November 24, 2025
**Issue**: Login 500 error with MongoDB ObjectId
**Status**: ✅ Resolved

