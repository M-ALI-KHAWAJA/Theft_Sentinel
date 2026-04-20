# AI Engine Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. File Structure Check
```bash
# Verify all files exist
ls apps/ai_engine/
ls apps/ai_engine/api/
ls apps/ai_engine/services/
ls apps/ai_engine/utils/
ls apps/ai_engine/migrations/

# Verify model files
ls ModelExport/yolov8l.pt
ls ModelExport/yolov8l-pose.pt
ls ModelExport/trained_models/theft_classifier.pkl
```

### 2. Database Migration
```bash
# Apply migrations
python manage.py migrate ai_engine

# Expected output:
# Running migrations:
#   Applying ai_engine.0001_initial... OK
```

### 3. Dependencies Check
```bash
# Verify all packages installed
pip list | grep -E "torch|ultralytics|opencv|deep-sort"

# Required:
# - torch>=2.0.0
# - ultralytics>=8.0.0
# - opencv-python>=4.8.0
# - deep-sort-realtime>=1.3.0
# - scikit-learn>=1.3.0
# - joblib>=1.3.0
```

### 4. Start Server
```bash
python manage.py runserver
```

**Expected Console Output:**
```
🚀 Initializing AI Engine...
✅ CUDA available: NVIDIA GeForce RTX 3050
📦 Loading detection model: ModelExport/yolov8l.pt
✅ Detection model loaded
📦 Loading pose model: ModelExport/yolov8l-pose.pt
✅ Pose model loaded
📦 Initializing DeepSORT tracker...
✅ DeepSORT initialized
📦 Loading ML classifier: ModelExport/trained_models/theft_classifier.pkl
🔮 ML theft classifier loaded.
✅ ML classifier loaded
🔥 Warming up models...
✅ Warmup complete
✅ AI Service initialized successfully!
```

### 5. Health Check
```bash
curl http://localhost:8000/api/ai/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "device": "cuda:0"
}
```

### 6. Authentication Test
```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Save the access token
TOKEN="<your_token_here>"
```

### 7. Model Info Test
```bash
curl http://localhost:8000/api/ai/model-info/ \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Simple Analysis Test
```bash
# Run test script
python test_ai_engine.py
```

## 🚀 Production Deployment

### 1. Environment Variables

Create/update `.env`:
```bash
# Django settings (existing)
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database (existing)
MONGO_URI=mongodb://your-mongo-uri
MONGO_DB_NAME=theft_sentinel

# AI Engine (optional)
AI_ENGINE_DEVICE=cuda:0
AI_ENGINE_CONFIDENCE_THRESHOLD=0.5
```

### 2. Gunicorn Configuration

Create `gunicorn_config.py`:
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2  # Keep low for GPU usage
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Longer timeout for AI processing

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "theft_sentinel"
```

### 3. Start with Gunicorn
```bash
gunicorn config.wsgi:application \
  --config gunicorn_config.py \
  --workers 2 \
  --timeout 300
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/theft_sentinel`:
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;  # For large frame uploads

    location /api/ai/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Longer timeout for AI processing
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Systemd Service

Create `/etc/systemd/system/theft_sentinel.service`:
```ini
[Unit]
Description=Theft Sentinel AI Backend
After=network.target

[Service]
Type=notify
User=your-user
Group=your-group
WorkingDirectory=/path/to/theft_sentinel_backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application \
    --config gunicorn_config.py \
    --workers 2 \
    --timeout 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable theft_sentinel
sudo systemctl start theft_sentinel
sudo systemctl status theft_sentinel
```

### 6. Monitoring

#### Log Monitoring
```bash
# Tail logs
sudo journalctl -u theft_sentinel -f

# Check for AI initialization
sudo journalctl -u theft_sentinel | grep "AI"
```

#### Performance Monitoring
```python
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor API performance
curl http://localhost:8000/api/ai/model-info/
```

## 🔒 Security Checklist

- [ ] DEBUG=False in production
- [ ] Secure SECRET_KEY set
- [ ] ALLOWED_HOSTS configured
- [ ] JWT tokens expire appropriately
- [ ] CORS configured for production domains
- [ ] File upload size limits set
- [ ] Rate limiting configured (optional)
- [ ] HTTPS enabled

## 📊 Performance Optimization

### 1. GPU Memory Management
```python
# In settings.py or ai_service.py
import torch
torch.backends.cudnn.benchmark = True
torch.cuda.empty_cache()  # Periodically clear cache
```

### 2. Worker Configuration
- Use 1-2 workers for GPU workloads
- More workers = more GPU memory usage
- Consider separate worker pool for AI endpoints

### 3. Caching
- Cache frequently accessed cameras
- Cache model outputs for duplicate frames
- Use Redis for distributed caching (optional)

### 4. Database Optimization
```python
# Index commonly queried fields
from apps.ai_engine.models import AIInference

# Already indexed:
# - timestamp
# - classification
# - camera_id
```

## 🧪 Testing in Production

### 1. Smoke Test
```bash
# Health check
curl https://your-domain.com/api/ai/health/

# Should return: {"status": "healthy", ...}
```

### 2. Load Test
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 100 -c 10 \
   -H "Authorization: Bearer $TOKEN" \
   https://your-domain.com/api/ai/model-info/
```

### 3. End-to-End Test
```bash
# Run full test suite
python test_ai_engine.py
```

## 🚨 Common Issues

### Issue: Models not loading
**Symptoms:** "AI service not initialized" error

**Solutions:**
1. Check model file paths exist
2. Verify CUDA availability: `python -c "import torch; print(torch.cuda.is_available())"`
3. Check logs: `journalctl -u theft_sentinel | grep AI`

### Issue: Slow inference
**Symptoms:** Processing time > 500ms

**Solutions:**
1. Verify GPU is being used: `nvidia-smi`
2. Reduce image resolution before sending
3. Check GPU memory not full: `torch.cuda.memory_summary()`
4. Reduce number of workers

### Issue: Out of memory
**Symptoms:** CUDA out of memory error

**Solutions:**
1. Reduce worker count to 1
2. Lower detection image size in config
3. Clear GPU cache periodically
4. Restart service: `sudo systemctl restart theft_sentinel`

### Issue: Frame decoding error
**Symptoms:** "Failed to decode frame from base64"

**Solutions:**
1. Verify base64 encoding is correct
2. Check image format (JPEG/PNG only)
3. Verify image not corrupted
4. Check max upload size in Nginx

## 📈 Monitoring Metrics

### Key Metrics to Track

1. **Processing Time**
   - Target: < 150ms on GPU
   - Alert if: > 500ms

2. **Theft Detection Rate**
   - Monitor false positives
   - Track confidence distribution

3. **API Availability**
   - Target: 99.9% uptime
   - Monitor via health endpoint

4. **GPU Utilization**
   - Target: 40-70% utilization
   - Alert if: > 90% sustained

5. **Alert Creation Rate**
   - Monitor alerts created per hour
   - Track alert → incident conversion

## ✅ Post-Deployment Checklist

- [ ] Health endpoint returns healthy
- [ ] All API endpoints accessible
- [ ] JWT authentication working
- [ ] Test frame analysis successful
- [ ] Camera processing functional
- [ ] Alerts created on theft detection
- [ ] Database migrations applied
- [ ] Logs show no errors
- [ ] GPU being utilized
- [ ] Response times acceptable
- [ ] Documentation accessible
- [ ] Team trained on new endpoints
- [ ] Monitoring configured
- [ ] Backup procedures in place

## 🎉 Deployment Complete!

Your AI Engine is now deployed and ready for production use!

For support, refer to:
- `AI_ENGINE_INTEGRATION.md` - Full documentation
- `AI_ENGINE_QUICKSTART.md` - Quick reference
- `example_usage.py` - Code examples
- `test_ai_engine.py` - Test suite

