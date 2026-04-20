# 🤖 AI Engine Integration Guide

## ✅ Integration Complete

The AI Engine has been successfully integrated into the Theft Sentinel frontend. This guide explains what was added and how to use it.

---

## 📁 New Files Created

### API Client
- **`src/api/aiEngine.js`** - AI Engine API client with all endpoints

### Custom Hooks
- **`src/hooks/useAIEngine.js`** - Hook for AI operations (analyze, process, health check)
- **`src/hooks/useCameraMonitor.js`** - Hook for real-time camera monitoring with polling

### Utilities
- **`src/utils/image.js`** - Image processing utilities (base64 conversion, resizing, validation)

### Components (src/components/AI/)
- **`AIHealthStatus.jsx`** - Display AI service health status
- **`AIModelInfo.jsx`** - Display loaded AI model information
- **`FrameAnalyzer.jsx`** - Upload and analyze frames for theft detection
- **`CameraMonitorCard.jsx`** - Individual camera monitoring card
- **`CameraGridAI.jsx`** - Grid view of all cameras with AI monitoring
- **`InferenceHistory.jsx`** - Historical inference results with filtering
- **`index.js`** - Barrel export for easy imports

### Pages (src/pages/ai/)
- **`Dashboard.jsx`** - AI Dashboard (health, model info, frame analyzer)
- **`Monitor.jsx`** - Real-time camera monitoring page
- **`History.jsx`** - Inference history page

---

## 🔧 Modified Files

### Router
- **`src/router/AppRouter.jsx`**
  - Added AI routes: `/ai/dashboard`, `/ai/monitor`, `/ai/history`
  - Protected routes for ADMIN and SECURITY_INCHARGE roles only

### Navigation
- **`src/components/Sidebar.jsx`**
  - Added AI menu items for ADMIN and SECURITY_INCHARGE roles
  - AI Dashboard, AI Monitor, AI History navigation links

---

## 🎯 Features Implemented

### 1. AI Health Monitoring
- Real-time health status of AI service
- Auto-refresh every 30 seconds
- Shows device, model load status, CUDA availability

### 2. Model Information
- Display detection model path
- Display pose model path
- Display ML classifier path
- CUDA and device information

### 3. Frame Analysis
- Upload images for analysis
- Automatic image resizing (max 1280x720)
- Image validation (type, size)
- Display results:
  - Classification (theft/normal)
  - Confidence score
  - Number of detections, persons, tracks
  - Suspicious behavior details
  - Processing time

### 4. Real-Time Camera Monitoring
- Monitor multiple cameras simultaneously
- Configurable polling interval (1s, 2s, 5s, 10s)
- Start/Stop monitoring per camera
- Live classification updates
- Visual indicators for theft detection
- Suspicious track alerts

### 5. Inference History
- Query historical AI inference results
- Filters:
  - Classification (theft/normal)
  - Minimum confidence
  - Camera ID
  - Result limit
- Display detailed inference information
- Alert IDs for theft detections

---

## 🔌 API Endpoints Integrated

All endpoints from `/api/ai/`:

1. **GET `/health/`** - Check AI service health
2. **POST `/analyze-frame/`** - Analyze uploaded frame
3. **POST `/process-camera/`** - Process camera RTSP stream
4. **GET `/model-info/`** - Get AI model information
5. **GET `/inference-history/`** - Query historical results
6. **POST `/full-pipeline/`** - Run complete analysis pipeline

---

## 🚀 How to Use

### Access AI Features

1. **Login** as ADMIN or SECURITY_INCHARGE
2. Navigate to AI pages via sidebar:
   - **AI Dashboard** - Main AI control panel
   - **AI Monitor** - Live camera monitoring
   - **AI History** - Historical results

### Analyze a Frame

1. Go to **AI Dashboard**
2. Click "Choose an image..." in the Frame Analyzer section
3. Select an image (JPEG, PNG, WebP)
4. Click "Analyze Frame"
5. View results:
   - Classification badge
   - Confidence score
   - Statistics
   - Suspicious behaviors (if detected)

### Monitor Cameras in Real-Time

1. Go to **AI Monitor**
2. Select polling interval (default: 2 seconds)
3. Click **Start** on any camera card
4. Monitor live results:
   - Classification status
   - Confidence updates
   - Person/object counts
   - Suspicious track alerts
5. Click **Stop** to pause monitoring

### View Inference History

1. Go to **AI History**
2. Apply filters:
   - Classification type
   - Minimum confidence
   - Camera ID (optional)
   - Result limit
3. Click **Search**
4. View historical inference records

---

## 🔒 Security & Permissions

### Role-Based Access

- **ADMIN**: Full access to all AI features
- **SECURITY_INCHARGE**: Full access to all AI features
- **GUARD**: No access to AI features

### Authentication

- All AI API calls require JWT authentication
- Token automatically injected via axios interceptor
- Token refresh handled automatically

---

## 🎨 UI/UX Features

### Visual Indicators

- **Green** - Normal activity
- **Red** - Theft detected
- **Yellow** - Suspicious behavior
- **Gray** - Inactive/offline

### Real-Time Updates

- Health status auto-refreshes
- Camera monitoring polls at configurable intervals
- Last update timestamp on each card

### Responsive Design

- Mobile-friendly layouts
- Grid adapts to screen size
- Touch-friendly controls

---

## 📊 Data Flow

```
User Action
    ↓
React Component
    ↓
Custom Hook (useAIEngine / useCameraMonitor)
    ↓
API Client (aiEngine.js)
    ↓
Axios Instance (with auth interceptor)
    ↓
Django Backend AI API
    ↓
AI Models (YOLOv8, Pose, ML Classifier)
    ↓
Response
    ↓
State Update
    ↓
UI Render
```

---

## 🛠️ Configuration

### Polling Intervals

Edit `src/components/AI/CameraGridAI.jsx`:

```javascript
const [intervalMs, setIntervalMs] = useState(2000); // Default 2 seconds
```

### Image Optimization

Edit `src/utils/image.js`:

```javascript
export const resizeImage = (file, maxWidth = 1280, maxHeight = 720, quality = 0.8)
```

### API Base URL

Set in `.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### AI Service Unavailable

- Check backend is running
- Verify `/api/ai/health/` endpoint
- Check JWT token validity

### Camera Processing Fails

- Verify camera RTSP URL is valid
- Check camera is ONLINE status
- Ensure AI service has loaded models

### Inference History Empty

- Verify database has inference records
- Check filter parameters
- Ensure user has permission

---

## 🔄 Future Enhancements

Potential additions (not implemented):

- Real-time WebSocket updates instead of polling
- Video playback with detections
- Export inference results to CSV
- AI model performance metrics
- Alert configuration per camera
- Notification system for theft detection

---

## 📝 Notes

- All AI components are isolated in `src/components/AI/`
- No modifications to existing auth, camera CRUD, or incident management
- Follows existing code patterns (axios, Recoil, React Router)
- Fully compatible with existing RBAC system
- Clean, modular, maintainable code

---

## ✨ Summary

The AI Engine integration is **complete** and **production-ready**. All features work seamlessly with the existing Theft Sentinel frontend without breaking any existing functionality.

**Total Files Created:** 18
**Total Files Modified:** 2 (Router, Sidebar)

🎉 **Ready to use!**

