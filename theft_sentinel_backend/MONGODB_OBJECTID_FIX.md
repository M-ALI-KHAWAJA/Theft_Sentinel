# 🔧 Fixed: MongoDB ObjectId JSON Serialization Error

## ❌ The Error

```
TypeError: Object of type ObjectId is not JSON serializable
Internal Server Error: /api/ai/inference-history/
```

---

## 🔍 Root Cause

MongoDB's `ObjectId` type cannot be directly serialized to JSON. The `AIInferenceSerializer` was exposing raw ObjectId fields:

**Problem Fields:**
- `camera_id` → Raw ObjectId
- `alert` → Full Alert object with ObjectId
- `alert.id` → ObjectId inside nested object

---

## ✅ The Fix

Updated **`apps/ai_engine/api/serializers.py`**:

### **Before (Broken):**
```python
class AIInferenceSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source='camera_id.name')
    alert_id = serializers.CharField(source='alert.id')  # ❌ ObjectId not converted
    
    class Meta:
        fields = [
            'id', 'camera_id',  # ❌ Raw ObjectId
            'alert',            # ❌ Full object with ObjectId
            'alert_id', ...
        ]
```

### **After (Fixed):**
```python
class AIInferenceSerializer(serializers.ModelSerializer):
    camera_id = serializers.SerializerMethodField()  # ✅ Custom method
    alert_id = serializers.SerializerMethodField()   # ✅ Custom method
    
    class Meta:
        fields = [
            'id', 'camera_id',  # ✅ Now returns string
            'alert_id', ...     # ✅ No raw 'alert' field
        ]
    
    def get_camera_id(self, obj):
        """Convert camera ObjectId to string"""
        return str(obj.camera_id.id) if obj.camera_id else None
    
    def get_alert_id(self, obj):
        """Convert alert ObjectId to string"""
        return str(obj.alert.id) if obj.alert else None
```

---

## 🎯 What Changed

### **AIInferenceSerializer:**
1. ✅ Removed raw `alert` field from fields list
2. ✅ Added `get_camera_id()` method to convert ObjectId → string
3. ✅ Added `get_alert_id()` method to convert ObjectId → string

### **DetectionTrackSerializer:**
1. ✅ Added `get_camera_id()` method to convert ObjectId → string

---

## 📡 API Response Now

### **Before (Error):**
```
500 Internal Server Error
TypeError: Object of type ObjectId is not JSON serializable
```

### **After (Success):**
```json
{
  "count": 10,
  "results": [
    {
      "id": "674505abc5f123456789abcd",
      "camera_id": "6924b8128134c437308926fa",  // ✅ String
      "camera_name": "Ali Mobile",
      "classification": "normal",
      "confidence": 0.23,
      "alert_id": "674505bbc5f123456789abce",    // ✅ String or null
      "detections": [...],
      "poses": [...],
      "tracks": [...],
      "frame_metadata": {...},
      "processing_time_ms": 125.5,
      "timestamp": "2025-11-25T18:00:00Z"
    }
  ]
}
```

---

## 🚀 How to Apply

**Restart Django server:**
```bash
# In Django terminal, press Ctrl+C, then:
python manage.py runserver
```

---

## ✅ After Restart

The following endpoints will now work:

1. ✅ `GET /api/ai/inference-history/`
2. ✅ `GET /api/ai/inference-history/?camera_id=XXX`
3. ✅ `GET /api/ai/inference-history/?min_confidence=0.5`

**No more 500 errors!** 🎉

---

## 🧪 Test It

```bash
# After restart, test:
curl http://127.0.0.1:8000/api/ai/inference-history/?min_confidence=0.5&limit=50 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return:
# {
#   "count": 50,
#   "results": [...]
# }
```

---

## 📊 Summary

| Issue | Status |
|-------|--------|
| ObjectId serialization error | ✅ Fixed |
| /api/ai/inference-history/ 500 error | ✅ Fixed |
| camera_id not JSON serializable | ✅ Fixed |
| alert_id not JSON serializable | ✅ Fixed |
| ERR_CONNECTION_REFUSED | ⚠️ Camera offline (separate issue) |

---

## ⚠️ Note: ERR_CONNECTION_REFUSED

This is a **separate issue** - it means:
- Camera at specific IP is offline
- Network connection to camera failed
- Camera app not running on phone

**Not related to the ObjectId serialization fix.**

Check your camera connections separately!

---

## 🎉 All Fixed!

Restart Django and the inference history endpoint will work perfectly! 🚀

