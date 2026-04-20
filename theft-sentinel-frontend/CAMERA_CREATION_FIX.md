# ✅ FIXED: Camera Creation 400 Error

## 🎯 Root Cause

The frontend was sending **wrong status values**:
- ❌ Sending: `"active"`, `"inactive"`, `"maintenance"`
- ✅ Backend expects: `"ONLINE"` or `"OFFLINE"`

Also sending `description` field that's not in the API schema.

---

## 🔧 What Was Fixed

### 1. Status Values Corrected

**Before (❌ Wrong):**
```javascript
status: 'active'  // Backend doesn't recognize this!

<option value="active">Active</option>
<option value="inactive">Inactive</option>
<option value="maintenance">Maintenance</option>
```

**After (✅ Correct):**
```javascript
status: 'ONLINE'  // Matches backend schema!

<option value="ONLINE">Online</option>
<option value="OFFLINE">Offline</option>
```

### 2. Removed Unsupported Field
- Removed `description` field (not in API schema)

### 3. Added Debug Logging
Added comprehensive error logging to diagnose validation issues:
```javascript
console.log('📤 [CreateCamera] Sending camera data:', formData);
console.error('❌ [CreateCamera] Error response:', error.response?.data);
```

---

## 📁 Files Fixed

1. ✅ **Create.jsx** - Status values and removed description
2. ✅ **Edit.jsx** - Status values and removed description

---

## 📋 Correct Camera Request Format

According to the official API schema:

```javascript
POST /api/cameras/
{
  "name": "string",
  "rtsp_url": "string",
  "location": "string",
  "zone": "string",
  "status": "ONLINE" | "OFFLINE"
}
```

**Required Fields:**
- `name` - Camera name
- `rtsp_url` - RTSP stream URL
- `location` - Physical location
- `zone` - Zone identifier
- `status` - Must be "ONLINE" or "OFFLINE"

---

## 🚀 Test Camera Creation Now

### Step 1: Refresh Browser
Press `Ctrl + Shift + R`

### Step 2: Create Camera
1. Login as Admin
2. Go to Cameras → "Add New Camera"
3. Fill in the form:
   - Name: "Test Camera"
   - RTSP URL: "rtsp://192.168.1.100:554/stream"
   - Location: "Main Entrance"
   - Zone: "Zone_A"
   - Status: Select "Online" or "Offline"
4. Click "Create Camera"

### Expected Result:
- ✅ Success toast: "Camera created successfully"
- ✅ Redirects to cameras list
- ✅ **No 400 error!**

---

## 🔍 If Still Getting Errors

### Check Browser Console
Open F12 → Console and look for:

```
📤 [CreateCamera] Sending camera data: {...}
❌ [CreateCamera] Error response: {...}
```

### Common Validation Errors:

#### 1. Name Already Exists
```
Error: "Name: Camera with this name already exists."
```
**Solution:** Use a different camera name

#### 2. Invalid RTSP URL
```
Error: "RTSP URL: Enter a valid URL."
```
**Solution:** Use format: `rtsp://ip:port/path`

#### 3. Invalid Status
```
Error: "Status: Invalid choice."
```
**Solution:** Should be fixed now (ONLINE or OFFLINE)

#### 4. Missing Required Field
```
Error: "This field is required."
```
**Solution:** Fill in all required fields (marked with *)

---

## ✅ Status Values Reference

| Frontend Display | Backend Value | Description |
|-----------------|---------------|-------------|
| Online | `ONLINE` | Camera is active and streaming |
| Offline | `OFFLINE` | Camera is inactive |

---

## 📊 Before vs After

### Before (❌ Causing 400 Error):
```json
{
  "name": "Camera 1",
  "rtsp_url": "rtsp://...",
  "location": "Entrance",
  "zone": "Zone A",
  "status": "active",        // ❌ Wrong!
  "description": "Test"      // ❌ Not in schema!
}
```

### After (✅ Working):
```json
{
  "name": "Camera 1",
  "rtsp_url": "rtsp://...",
  "location": "Entrance",
  "zone": "Zone A",
  "status": "ONLINE"         // ✅ Correct!
}
```

---

## 🎯 Summary

**Problem:** Frontend sending wrong status values and extra field
**Solution:** Changed status to ONLINE/OFFLINE, removed description field
**Status:** ✅ **FIXED!**

---

**Camera creation should now work without 400 errors!** 🎉

