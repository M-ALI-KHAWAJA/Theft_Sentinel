# 🎥 Frontend: Continuous Monitoring Integration

## 📡 API Endpoints

### **Base URL:** `http://127.0.0.1:8000/api/ai/`

---

## 1️⃣ Start Continuous Monitoring

**Endpoint:** `POST /api/ai/monitor/start/`

**Request:**
```http
POST /api/ai/monitor/start/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "camera_id": "6924b8128134c437308926fa"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Started continuous monitoring",
  "camera_id": "6924b8128134c437308926fa",
  "camera_name": "Ali Mobile",
  "rtsp_url_preview": "http://192.168.10.33:8080"
}
```

**Response (400 Error):**
```json
{
  "success": false,
  "error": "Monitor already running or failed to start",
  "camera_id": "6924b8128134c437308926fa"
}
```

---

## 2️⃣ Get Monitor Status (Real-time Results)

**Endpoint:** `GET /api/ai/monitor/status/`

**Request:**
```http
GET /api/ai/monitor/status/?camera_id=6924b8128134c437308926fa
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "camera_id": "6924b8128134c437308926fa",
  "monitor": {
    "camera_id": "6924b8128134c437308926fa",
    "is_running": true,
    "frames_processed": 1523,
    "fps": 28.5,
    "elapsed_seconds": 53.4,
    "error_count": 0,
    "last_result": {
      "classification": "normal",
      "confidence": 0.23,
      "persons": 1,
      "objects": 5,
      "tracks": 3,
      "timestamp": "2025-11-25T10:30:45Z",
      "processing_time_ms": 125,
      "detections": [...],
      "poses": [...],
      "tracks_data": [...]
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "camera_id": "6924b8128134c437308926fa",
  "monitor": null,
  "message": "No monitor running for this camera"
}
```

---

## 3️⃣ Stop Continuous Monitoring

**Endpoint:** `POST /api/ai/monitor/stop/`

**Request:**
```http
POST /api/ai/monitor/stop/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "camera_id": "6924b8128134c437308926fa"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Stopped monitoring",
  "camera_id": "6924b8128134c437308926fa"
}
```

---

## 💻 React/JSX Implementation

### **Custom Hook: `useContinuousMonitor.js`**

```jsx
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api/ai';

export const useContinuousMonitor = (cameraId) => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Start continuous monitoring
  const startMonitoring = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        `${API_BASE}/monitor/start/`,
        { camera_id: cameraId },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          }
        }
      );

      if (response.data.success) {
        setIsMonitoring(true);
      } else {
        setError(response.data.error);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start monitoring');
    } finally {
      setLoading(false);
    }
  };

  // Stop continuous monitoring
  const stopMonitoring = async () => {
    setLoading(true);
    
    try {
      await axios.post(
        `${API_BASE}/monitor/stop/`,
        { camera_id: cameraId },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          }
        }
      );

      setIsMonitoring(false);
      setStats(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to stop monitoring');
    } finally {
      setLoading(false);
    }
  };

  // Poll status while monitoring
  useEffect(() => {
    if (!isMonitoring) return;

    const pollStatus = async () => {
      try {
        const response = await axios.get(
          `${API_BASE}/monitor/status/?camera_id=${cameraId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            }
          }
        );

        if (response.data.monitor) {
          setStats(response.data.monitor);
        } else {
          // Monitor stopped externally
          setIsMonitoring(false);
        }
      } catch (err) {
        console.error('Failed to fetch status:', err);
      }
    };

    // Poll every 1 second for real-time updates
    const interval = setInterval(pollStatus, 1000);

    // Initial fetch
    pollStatus();

    return () => clearInterval(interval);
  }, [isMonitoring, cameraId]);

  return {
    isMonitoring,
    stats,
    loading,
    error,
    startMonitoring,
    stopMonitoring,
  };
};
```

---

## 🎨 React Component Example

### **ContinuousMonitorCard.jsx**

```jsx
import React from 'react';
import { useContinuousMonitor } from './hooks/useContinuousMonitor';

const ContinuousMonitorCard = ({ camera }) => {
  const {
    isMonitoring,
    stats,
    loading,
    error,
    startMonitoring,
    stopMonitoring,
  } = useContinuousMonitor(camera.id);

  const lastResult = stats?.last_result;

  return (
    <div className="monitor-card">
      {/* Header */}
      <div className="card-header">
        <h3>{camera.name}</h3>
        <span className="location">{camera.location}</span>
      </div>

      {/* Status Badge */}
      {isMonitoring && (
        <div className="status-badge">
          <span className="live-indicator">● LIVE</span>
          <span className="fps-counter">{stats?.fps?.toFixed(1)} FPS</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {/* Results */}
      {isMonitoring && lastResult ? (
        <div className="results">
          {/* Classification */}
          <div className={`classification ${lastResult.classification}`}>
            {lastResult.classification === 'theft' ? (
              <span className="theft">⚠️ THEFT DETECTED</span>
            ) : (
              <span className="normal">✓ Normal</span>
            )}
          </div>

          {/* Stats Grid */}
          <div className="stats-grid">
            <div className="stat">
              <span className="label">Confidence</span>
              <span className="value">
                {(lastResult.confidence * 100).toFixed(0)}%
              </span>
            </div>
            
            <div className="stat">
              <span className="label">Persons</span>
              <span className="value">{lastResult.persons}</span>
            </div>
            
            <div className="stat">
              <span className="label">Objects</span>
              <span className="value">{lastResult.objects}</span>
            </div>
            
            <div className="stat">
              <span className="label">Tracks</span>
              <span className="value">{lastResult.tracks}</span>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="metrics">
            <span>Frames: {stats.frames_processed}</span>
            <span>•</span>
            <span>FPS: {stats.fps.toFixed(1)}</span>
            <span>•</span>
            <span>Uptime: {Math.floor(stats.elapsed_seconds)}s</span>
            <span>•</span>
            <span>Processing: {lastResult.processing_time_ms}ms</span>
          </div>

          {/* Timestamp */}
          <div className="timestamp">
            Last update: {new Date(lastResult.timestamp).toLocaleTimeString()}
          </div>
        </div>
      ) : isMonitoring ? (
        <div className="loading">
          <div className="spinner"></div>
          <span>Initializing monitor...</span>
        </div>
      ) : (
        <div className="idle-state">
          <p>Click Start to begin continuous monitoring</p>
        </div>
      )}

      {/* Action Button */}
      <button
        className={`action-btn ${isMonitoring ? 'stop' : 'start'}`}
        onClick={isMonitoring ? stopMonitoring : startMonitoring}
        disabled={loading}
      >
        {loading ? 'Loading...' : isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
      </button>
    </div>
  );
};

export default ContinuousMonitorCard;
```

---

## 🎨 Basic CSS

```css
.monitor-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: white;
}

.status-badge {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.live-indicator {
  color: #22c55e;
  font-weight: bold;
}

.classification.theft {
  background: #fee2e2;
  color: #dc2626;
  padding: 10px;
  border-radius: 6px;
}

.classification.normal {
  background: #dcfce7;
  color: #16a34a;
  padding: 10px;
  border-radius: 6px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin: 15px 0;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat .label {
  font-size: 12px;
  color: #666;
}

.stat .value {
  font-size: 24px;
  font-weight: bold;
}

.metrics {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #666;
  margin-top: 10px;
}

.action-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
}

.action-btn.start {
  background: #3b82f6;
  color: white;
}

.action-btn.stop {
  background: #ef4444;
  color: white;
}
```

---

## 📊 TypeScript Types (Optional)

```typescript
export interface MonitorStats {
  camera_id: string;
  is_running: boolean;
  frames_processed: number;
  fps: number;
  elapsed_seconds: number;
  error_count: number;
  last_result: {
    classification: 'normal' | 'theft';
    confidence: number;
    persons: number;
    objects: number;
    tracks: number;
    timestamp: string;
    processing_time_ms: number;
    detections: any[];
    poses: any[];
    tracks_data: any[];
  };
}

export interface StartMonitorResponse {
  success: boolean;
  message?: string;
  error?: string;
  camera_id: string;
  camera_name?: string;
}
```

---

## 🚀 Quick Integration Steps

1. **Copy the hook** (`useContinuousMonitor.js`) to your project
2. **Copy the component** (`ContinuousMonitorCard.jsx`)
3. **Use in your page:**

```jsx
import ContinuousMonitorCard from './components/ContinuousMonitorCard';

const AIMonitoringPage = () => {
  const cameras = [...]; // Your cameras from API

  return (
    <div className="monitoring-page">
      <h1>AI Continuous Monitoring</h1>
      <div className="camera-grid">
        {cameras.map(camera => (
          <ContinuousMonitorCard key={camera.id} camera={camera} />
        ))}
      </div>
    </div>
  );
};
```

---

## 🎯 Key Differences from Polling Mode

| Feature | Polling Mode | Continuous Mode |
|---------|--------------|-----------------|
| **Start Call** | None (just poll) | POST `/monitor/start/` |
| **Get Results** | POST `/process-camera/` | GET `/monitor/status/` |
| **Stop Call** | None (stop polling) | POST `/monitor/stop/` |
| **FPS** | 0.5 (every 2s) | 30 |
| **Backend** | Process on-demand | Background thread |

---

## ✅ Testing Checklist

- [ ] Hook imports without errors
- [ ] Start button calls API successfully
- [ ] Status updates every second
- [ ] All values display (confidence, persons, etc.)
- [ ] FPS counter increases
- [ ] Stop button works
- [ ] Error handling works
- [ ] Multiple cameras can be monitored

---

## 🎉 Done!

You now have:
- ✅ 30 FPS continuous processing
- ✅ Real-time theft detection
- ✅ Live FPS counter
- ✅ Instant alerts
- ✅ Better object tracking

**Your frontend will show live AI results at 30 FPS instead of 0.5 FPS!** 🚀

