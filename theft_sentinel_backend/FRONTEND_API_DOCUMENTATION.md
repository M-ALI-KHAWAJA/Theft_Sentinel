# 🎨 AI Engine API - Frontend Integration Guide

> **Complete guide for React + Vite frontend developers**

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [TypeScript Types](#typescript-types)
4. [React Examples](#react-examples)
5. [Custom Hooks](#custom-hooks)
6. [Complete Components](#complete-components)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Installation

```bash
npm install axios
# or
npm install  # if using native fetch
```

### Setup TypeScript Types

Copy `api-types.ts` to your project:

```typescript
// src/types/ai-api.ts
import { AIEngineAPI } from './api-types';

export const aiAPI = new AIEngineAPI(
  'http://localhost:8000/api/ai/',
  localStorage.getItem('access_token')
);
```

---

## 📡 API Endpoints

### Base URL
```
http://localhost:8000/api/ai/
```

### Authentication
All endpoints except `/health/` require JWT token in header:
```
Authorization: Bearer <your_jwt_token>
```

---

### 1. 🏥 Health Check

**Endpoint:** `GET /api/ai/health/`

**Authentication:** Not required

**Purpose:** Check if AI service is ready

**Request:**
```typescript
const response = await fetch('http://localhost:8000/api/ai/health/');
const data = await response.json();
```

**Response:**
```typescript
{
  "status": "healthy" | "initializing",
  "models_loaded": true,
  "device": "cuda:0"
}
```

**React Example:**
```typescript
import { useState, useEffect } from 'react';

function HealthStatus() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/ai/health/')
      .then(res => res.json())
      .then(data => {
        setHealth(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Checking AI service...</div>;
  
  return (
    <div className={health.status === 'healthy' ? 'text-green-500' : 'text-yellow-500'}>
      Status: {health.status}
      <br />
      Models Loaded: {health.models_loaded ? '✓' : '✗'}
      <br />
      Device: {health.device}
    </div>
  );
}
```

---

### 2. 🖼️ Analyze Frame

**Endpoint:** `POST /api/ai/analyze-frame/`

**Authentication:** Required

**Purpose:** Analyze a single frame for theft detection

**Request:**
```typescript
interface AnalyzeFrameRequest {
  frame: string;                    // Base64 encoded image
  camera_id?: string;               // Optional
  save_to_db?: boolean;            // Default: true
  create_alert_on_theft?: boolean; // Default: true
}
```

**Response:**
```typescript
interface AnalysisResponse {
  detections: Detection[];          // Detected objects
  poses: Pose[];                    // Pose keypoints
  tracks: Track[];                  // Tracked objects
  classification: 'theft' | 'normal';
  confidence: number;               // 0-1
  suspicious_tracks: SuspiciousTrack[];
  frame_metadata: FrameMetadata;
  processing_time_ms: number;
  alert_created?: boolean;
  alert_id?: string;
  inference_id?: string;
}
```

**React Example:**
```typescript
import { useState } from 'react';

function FrameAnalyzer() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeImage = async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      // Convert to base64
      const base64 = await fileToBase64(file);

      // Call API
      const response = await fetch('http://localhost:8000/api/ai/analyze-frame/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          frame: base64,
          save_to_db: false,
          create_alert_on_theft: false,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      analyzeImage(file);
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFileSelect} />
      
      {loading && <div>Analyzing...</div>}
      {error && <div className="text-red-500">Error: {error}</div>}
      
      {result && (
        <div className="mt-4">
          <div className="text-lg font-bold">
            Classification: {result.classification.toUpperCase()}
          </div>
          <div>Confidence: {(result.confidence * 100).toFixed(1)}%</div>
          <div>Detections: {result.detections.length}</div>
          <div>Processing Time: {result.processing_time_ms.toFixed(1)}ms</div>
          
          {result.classification === 'theft' && (
            <div className="mt-2 p-4 bg-red-100 border border-red-500">
              ⚠️ THEFT DETECTED!
              {result.alert_created && (
                <div className="mt-2">Alert created: {result.alert_id}</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper function
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1]; // Remove data URL prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
```

---

### 3. 📹 Process Camera

**Endpoint:** `POST /api/ai/process-camera/`

**Authentication:** Required

**Purpose:** Capture and analyze frame from camera RTSP stream

**Request:**
```typescript
interface ProcessCameraRequest {
  camera_id: string;                // Required
  save_to_db?: boolean;            // Default: true
  create_alert_on_theft?: boolean; // Default: true
}
```

**Response:** Same as Analyze Frame + camera details

**React Example:**
```typescript
import { useState } from 'react';

function CameraMonitor({ cameraId }: { cameraId: string }) {
  const [result, setResult] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const processCamera = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ai/process-camera/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          camera_id: cameraId,
          save_to_db: true,
          create_alert_on_theft: true,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error processing camera:', error);
    }
  };

  const startMonitoring = () => {
    setIsMonitoring(true);
    const interval = setInterval(processCamera, 1000); // Every second
    return () => clearInterval(interval);
  };

  return (
    <div className="p-4 border rounded">
      <h3>Camera: {result?.camera_name || cameraId}</h3>
      
      <button
        onClick={startMonitoring}
        disabled={isMonitoring}
        className="px-4 py-2 bg-blue-500 text-white rounded"
      >
        {isMonitoring ? 'Monitoring...' : 'Start Monitoring'}
      </button>

      {result && (
        <div className="mt-4">
          <div className={`text-lg font-bold ${
            result.classification === 'theft' ? 'text-red-500' : 'text-green-500'
          }`}>
            {result.classification === 'theft' ? '🚨 THEFT DETECTED' : '✓ Normal'}
          </div>
          <div>Confidence: {(result.confidence * 100).toFixed(1)}%</div>
          <div>Persons: {result.frame_metadata.num_persons}</div>
          <div>Objects: {result.frame_metadata.num_detections}</div>
        </div>
      )}
    </div>
  );
}
```

---

### 4. 📊 Model Info

**Endpoint:** `GET /api/ai/model-info/`

**Authentication:** Required

**Purpose:** Get information about loaded AI models

**Request:**
```typescript
const response = await fetch('http://localhost:8000/api/ai/model-info/', {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

**Response:**
```typescript
{
  "detection_model": "ModelExport/yolov8l.pt",
  "pose_model": "ModelExport/yolov8l-pose.pt",
  "ml_classifier": "ModelExport/trained_models/theft_classifier.pkl",
  "device": "cuda:0",
  "cuda_available": true,
  "models_loaded": true,
  "ml_classifier_loaded": true
}
```

**React Example:**
```typescript
function ModelStatus() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/ai/model-info/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    })
      .then(res => res.json())
      .then(setInfo);
  }, []);

  if (!info) return <div>Loading...</div>;

  return (
    <div className="bg-gray-100 p-4 rounded">
      <h3 className="font-bold mb-2">AI Model Status</h3>
      <div className="space-y-1">
        <div>Device: <span className="font-mono">{info.device}</span></div>
        <div>CUDA: {info.cuda_available ? '✓' : '✗'}</div>
        <div>Models Loaded: {info.models_loaded ? '✓' : '✗'}</div>
        <div>ML Classifier: {info.ml_classifier_loaded ? '✓' : '✗'}</div>
      </div>
    </div>
  );
}
```

---

### 5. 📜 Inference History

**Endpoint:** `GET /api/ai/inference-history/`

**Authentication:** Required

**Purpose:** Query historical inference results

**Query Parameters:**
```typescript
interface InferenceHistoryParams {
  camera_id?: string;
  classification?: 'theft' | 'normal';
  min_confidence?: number;  // 0-1
  limit?: number;           // Max 500
}
```

**Request:**
```typescript
const params = new URLSearchParams({
  classification: 'theft',
  min_confidence: '0.7',
  limit: '20',
});

const response = await fetch(
  `http://localhost:8000/api/ai/inference-history/?${params}`,
  {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  }
);
```

**Response:**
```typescript
{
  "count": 15,
  "results": [
    {
      "id": "inference_123",
      "camera_id": "camera_456",
      "camera_name": "Main Entrance",
      "classification": "theft",
      "confidence": 0.87,
      "timestamp": "2025-11-25T19:45:00Z",
      "alert_id": "alert_789",
      // ... other fields
    }
  ]
}
```

**React Example:**
```typescript
import { useState, useEffect } from 'react';

function InferenceHistory() {
  const [history, setHistory] = useState([]);
  const [filters, setFilters] = useState({
    classification: 'theft',
    minConfidence: 0.5,
    limit: 20,
  });

  useEffect(() => {
    const params = new URLSearchParams({
      classification: filters.classification,
      min_confidence: filters.minConfidence.toString(),
      limit: filters.limit.toString(),
    });

    fetch(`http://localhost:8000/api/ai/inference-history/?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    })
      .then(res => res.json())
      .then(data => setHistory(data.results));
  }, [filters]);

  return (
    <div>
      <div className="mb-4 flex gap-4">
        <select
          value={filters.classification}
          onChange={(e) => setFilters({ ...filters, classification: e.target.value })}
          className="border rounded px-2 py-1"
        >
          <option value="">All</option>
          <option value="theft">Theft</option>
          <option value="normal">Normal</option>
        </select>

        <input
          type="number"
          min="0"
          max="1"
          step="0.1"
          value={filters.minConfidence}
          onChange={(e) => setFilters({ ...filters, minConfidence: parseFloat(e.target.value) })}
          placeholder="Min Confidence"
          className="border rounded px-2 py-1"
        />
      </div>

      <div className="space-y-2">
        {history.map((inference) => (
          <div
            key={inference.id}
            className={`p-4 border rounded ${
              inference.classification === 'theft' ? 'bg-red-50 border-red-300' : 'bg-green-50'
            }`}
          >
            <div className="flex justify-between">
              <span className="font-bold">{inference.camera_name}</span>
              <span className="text-sm text-gray-500">
                {new Date(inference.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="mt-1">
              Classification: {inference.classification}
              {' | '}
              Confidence: {(inference.confidence * 100).toFixed(1)}%
            </div>
            {inference.alert_id && (
              <div className="mt-1 text-sm text-red-600">
                Alert ID: {inference.alert_id}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🎣 Custom React Hooks

### useAIEngine Hook

```typescript
// hooks/useAIEngine.ts
import { useState, useCallback } from 'react';
import { AIEngineAPI, AnalysisResponse, AnalyzeFrameRequest } from '../types/ai-api';

export function useAIEngine() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);

  const api = new AIEngineAPI(
    'http://localhost:8000/api/ai/',
    localStorage.getItem('access_token')
  );

  const analyzeFrame = useCallback(async (request: AnalyzeFrameRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.analyzeFrame(request);
      setResult(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const processCamera = useCallback(async (cameraId: string, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.processCamera({
        camera_id: cameraId,
        ...options,
      });
      setResult(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    loading,
    error,
    result,
    analyzeFrame,
    processCamera,
    reset,
  };
}
```

**Usage:**
```typescript
function MyComponent() {
  const { loading, error, result, analyzeFrame } = useAIEngine();

  const handleAnalyze = async (file: File) => {
    const base64 = await fileToBase64(file);
    await analyzeFrame({ frame: base64 });
  };

  return (
    <div>
      {loading && <div>Processing...</div>}
      {error && <div>Error: {error}</div>}
      {result && <div>Classification: {result.classification}</div>}
    </div>
  );
}
```

---

### useCameraMonitor Hook

```typescript
// hooks/useCameraMonitor.ts
import { useState, useEffect, useRef } from 'react';
import { AIEngineAPI, AnalysisResponse } from '../types/ai-api';

export function useCameraMonitor(cameraId: string, intervalMs: number = 1000) {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [currentResult, setCurrentResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const api = new AIEngineAPI(
    'http://localhost:8000/api/ai/',
    localStorage.getItem('access_token')
  );

  const processFrame = async () => {
    try {
      const result = await api.processCamera({
        camera_id: cameraId,
        save_to_db: true,
        create_alert_on_theft: true,
      });
      setCurrentResult(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const start = () => {
    if (!isMonitoring) {
      setIsMonitoring(true);
      processFrame(); // Process immediately
      intervalRef.current = window.setInterval(processFrame, intervalMs);
    }
  };

  const stop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsMonitoring(false);
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isMonitoring,
    currentResult,
    error,
    start,
    stop,
  };
}
```

**Usage:**
```typescript
function CameraMonitor({ cameraId }: { cameraId: string }) {
  const { isMonitoring, currentResult, error, start, stop } = useCameraMonitor(cameraId, 1000);

  return (
    <div>
      <button onClick={isMonitoring ? stop : start}>
        {isMonitoring ? 'Stop' : 'Start'} Monitoring
      </button>
      
      {error && <div className="text-red-500">{error}</div>}
      
      {currentResult && (
        <div className={currentResult.classification === 'theft' ? 'text-red-500' : 'text-green-500'}>
          {currentResult.classification.toUpperCase()}
          ({(currentResult.confidence * 100).toFixed(1)}%)
        </div>
      )}
    </div>
  );
}
```

---

## 🎨 Complete Components

### Complete Theft Detection Dashboard

```typescript
// components/TheftDetectionDashboard.tsx
import { useState } from 'react';
import { useAIEngine } from '../hooks/useAIEngine';
import { fileToBase64, resizeImage } from '../utils/image';

export function TheftDetectionDashboard() {
  const { loading, error, result, analyzeFrame } = useAIEngine();
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    setPreview(URL.createObjectURL(file));

    // Resize image for better performance
    const resized = await resizeImage(file, 1280, 720);
    const base64 = await fileToBase64(new File([resized], file.name));

    // Analyze
    await analyzeFrame({
      frame: base64,
      save_to_db: true,
      create_alert_on_theft: true,
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Theft Detection Analysis</h1>

      {/* Upload Section */}
      <div className="mb-6">
        <label className="block mb-2 font-semibold">Upload Frame</label>
        <input
          type="file"
          accept="image/*"
          onChange={handleFileUpload}
          className="block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100"
        />
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-2">Analyzing frame...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-300 rounded p-4 mb-6">
          <p className="text-red-700">❌ Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Image Preview */}
          {preview && (
            <div>
              <h3 className="font-semibold mb-2">Analyzed Frame</h3>
              <img src={preview} alt="Preview" className="w-full rounded border" />
            </div>
          )}

          {/* Analysis Results */}
          <div>
            <h3 className="font-semibold mb-4">Analysis Results</h3>

            {/* Classification Badge */}
            <div className={`mb-4 p-4 rounded ${
              result.classification === 'theft'
                ? 'bg-red-100 border border-red-500'
                : 'bg-green-100 border border-green-500'
            }`}>
              <div className="text-2xl font-bold">
                {result.classification === 'theft' ? '🚨 THEFT DETECTED' : '✓ Normal Activity'}
              </div>
              <div className="mt-1">
                Confidence: {(result.confidence * 100).toFixed(1)}%
              </div>
            </div>

            {/* Stats */}
            <div className="space-y-2 mb-4">
              <div className="flex justify-between">
                <span>Detections:</span>
                <span className="font-semibold">{result.detections.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Persons:</span>
                <span className="font-semibold">{result.frame_metadata.num_persons}</span>
              </div>
              <div className="flex justify-between">
                <span>Tracks:</span>
                <span className="font-semibold">{result.tracks.length}</span>
              </div>
              <div className="flex justify-between">
                <span>Processing Time:</span>
                <span className="font-semibold">{result.processing_time_ms.toFixed(1)}ms</span>
              </div>
            </div>

            {/* Suspicious Tracks */}
            {result.suspicious_tracks.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-300 rounded p-4">
                <h4 className="font-semibold mb-2">⚠️ Suspicious Behavior Detected</h4>
                {result.suspicious_tracks.map((track) => (
                  <div key={track.track_id} className="mb-2">
                    <div className="font-semibold">Track #{track.track_id}</div>
                    <div className="text-sm">Score: {(track.ml_score * 100).toFixed(1)}%</div>
                    <div className="text-xs text-gray-600">
                      Hand in bag: {track.behavior.hand_in_bag} frames
                      {' | '}
                      Concealment events: {track.behavior.concealment_events}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Alert Info */}
            {result.alert_created && (
              <div className="mt-4 bg-orange-50 border border-orange-300 rounded p-4">
                <div className="font-semibold">📢 Alert Created</div>
                <div className="text-sm">ID: {result.alert_id}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Real-Time Camera Grid

```typescript
// components/CameraGrid.tsx
import { useCameraMonitor } from '../hooks/useCameraMonitor';

interface CameraCardProps {
  cameraId: string;
  cameraName: string;
}

function CameraCard({ cameraId, cameraName }: CameraCardProps) {
  const { isMonitoring, currentResult, error, start, stop } = useCameraMonitor(cameraId, 2000);

  return (
    <div className="border rounded-lg p-4 bg-white shadow">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">{cameraName}</h3>
        <button
          onClick={isMonitoring ? stop : start}
          className={`px-3 py-1 rounded text-sm ${
            isMonitoring
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {isMonitoring ? 'Stop' : 'Start'}
        </button>
      </div>

      {error && (
        <div className="text-red-500 text-sm mb-2">Error: {error}</div>
      )}

      {currentResult && (
        <div>
          <div className={`text-lg font-bold ${
            currentResult.classification === 'theft' ? 'text-red-500' : 'text-green-500'
          }`}>
            {currentResult.classification === 'theft' ? '🚨 THEFT' : '✓ Normal'}
          </div>
          <div className="text-sm text-gray-600">
            Confidence: {(currentResult.confidence * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">
            Persons: {currentResult.frame_metadata.num_persons}
          </div>
          <div className="text-sm text-gray-600">
            Objects: {currentResult.frame_metadata.num_detections}
          </div>
        </div>
      )}

      {isMonitoring && !currentResult && (
        <div className="text-gray-500">Waiting for data...</div>
      )}
    </div>
  );
}

export function CameraGrid({ cameras }: { cameras: Array<{ id: string; name: string }> }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
      {cameras.map((camera) => (
        <CameraCard
          key={camera.id}
          cameraId={camera.id}
          cameraName={camera.name}
        />
      ))}
    </div>
  );
}
```

---

## 🎯 Best Practices

### 1. Image Optimization

```typescript
// Always resize images before sending
const optimizedFile = await resizeImage(file, 1280, 720, 0.8);
const base64 = await fileToBase64(optimizedFile);
```

### 2. Error Handling

```typescript
try {
  const result = await api.analyzeFrame({ frame: base64 });
  // Handle success
} catch (error) {
  if (error.message.includes('401')) {
    // Redirect to login
    router.push('/login');
  } else {
    // Show error to user
    toast.error(error.message);
  }
}
```

### 3. Token Management

```typescript
// Store token after login
localStorage.setItem('access_token', token);

// Update API token
api.setToken(token);

// Clear on logout
localStorage.removeItem('access_token');
```

### 4. Polling Best Practices

```typescript
// Use intervals wisely
const FAST_POLL = 1000;    // 1 second for critical cameras
const NORMAL_POLL = 2000;  // 2 seconds for regular monitoring
const SLOW_POLL = 5000;    // 5 seconds for background monitoring

// Clean up intervals
useEffect(() => {
  const interval = setInterval(poll, NORMAL_POLL);
  return () => clearInterval(interval);
}, []);
```

---

## 📦 Complete Project Setup

### Install

```bash
npm create vite@latest my-theft-detection -- --template react-ts
cd my-theft-detection
npm install
npm install axios
```

### Project Structure

```
src/
├── api/
│   └── ai-engine.ts         # API client
├── hooks/
│   ├── useAIEngine.ts       # Main hook
│   └── useCameraMonitor.ts  # Camera monitoring
├── components/
│   ├── TheftDetectionDashboard.tsx
│   ├── CameraGrid.tsx
│   └── InferenceHistory.tsx
├── types/
│   └── ai-api.ts            # TypeScript types
├── utils/
│   └── image.ts             # Image utilities
└── App.tsx
```

---

## 🎉 Summary

**6 API Endpoints:**
1. ✅ Health Check - `GET /api/ai/health/`
2. ✅ Analyze Frame - `POST /api/ai/analyze-frame/`
3. ✅ Process Camera - `POST /api/ai/process-camera/`
4. ✅ Model Info - `GET /api/ai/model-info/`
5. ✅ Inference History - `GET /api/ai/inference-history/`
6. ✅ Full Pipeline - `POST /api/ai/full-pipeline/`

**Provided:**
- ✅ Complete TypeScript types
- ✅ API client class
- ✅ Custom React hooks
- ✅ Complete components
- ✅ Error handling patterns
- ✅ Best practices
- ✅ Example usage

**Ready for production! 🚀**

