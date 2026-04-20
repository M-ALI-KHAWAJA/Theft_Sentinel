# Theft Sentinel - AI Powered Anti-Theft System (Backend)

Complete Django REST API backend for the Theft Sentinel MVP, built with Django, DRF, SimpleJWT, and MongoDB (via Djongo).

## 🏗️ Architecture

- **Framework**: Django 4.2.7 + Django REST Framework
- **Database**: MongoDB (via Djongo ORM)
- **Authentication**: JWT (SimpleJWT)
- **Notifications**: Twilio (SMS) + Email (SMTP)

## 📦 Project Structure

```
theft_sentinel_backend/
├── config/
│   ├── settings.py          # Main settings with MongoDB + JWT config
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/            # User authentication & role-based access
│   ├── personnel/           # Staff profiles with zone assignments
│   ├── cameras/             # Camera management with CRUD
│   ├── surveillance/        # AI event ingestion + processing
│   ├── tracking/            # Person tracking with feature vectors
│   ├── alerts/              # Alert management & acknowledgement
│   ├── incidents/           # Incident workflow (CREATED→ASSIGNED→ACK→RESOLVED)
│   ├── mobile/              # SMS/Email notifications (Twilio)
│   ├── dashboard/           # Statistics & analytics APIs
│   └── feedback/            # User feedback (GENERAL, FALSE_POSITIVE, etc.)
└── manage.py
```

## 🗄️ Database Schema

### Collections

1. **User** - Custom user with roles (ADMIN, SECURITY_INCHARGE, GUARD)
2. **Personnel** - Staff profiles with assigned zones
3. **Camera** - Surveillance cameras with RTSP URLs
4. **Alert** - Security alerts with severity levels
5. **Incident** - Incident tracking with status workflow
6. **Feedback** - User feedback on system performance
7. **TrackingRecord** - Person tracking feature vectors
8. **SurveillanceEvent** - AI-detected events
9. **Notification** - SMS/Email notification logs

## 🚀 Setup Instructions

### 1. Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Twilio account (for SMS)
- SMTP credentials (for Email)

### 2. Installation

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
# Windows Git Bash:
source env/Scripts/activate
# Linux/Mac:
source env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=theft_sentinel

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 4. Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## 🔐 Authentication

### JWT Token Flow

1. **Register**: `POST /api/auth/register/`
2. **Login**: `POST /api/auth/login/` → Returns `access` and `refresh` tokens
3. **Refresh**: `POST /api/auth/refresh/` → Get new access token
4. **Logout**: `POST /api/auth/logout/` → Blacklist refresh token

### Authorization Header

```
Authorization: Bearer <access_token>
```

## 📡 API Endpoints

### Authentication (`/api/auth/`)
- `POST /register/` - User registration
- `POST /login/` - Login (returns JWT tokens)
- `POST /refresh/` - Refresh access token
- `POST /logout/` - Logout (blacklist token)
- `GET /profile/` - Get current user profile
- `PUT /profile/` - Update profile
- `POST /change-password/` - Change password
- `GET /users/` - List users (Admin only)

### Personnel (`/api/personnel/`)
- `GET /` - List personnel
- `POST /` - Create personnel (Admin only)
- `GET /{id}/` - Get personnel details
- `PUT /{id}/` - Update personnel (Admin only)
- `DELETE /{id}/` - Delete personnel (Admin only)
- `GET /me/` - Get current user's personnel profile

### Cameras (`/api/cameras/`)
- `GET /` - List cameras
- `POST /` - Create camera (Admin only)
- `GET /{id}/` - Get camera details
- `PUT /{id}/` - Update camera (Admin only)
- `DELETE /{id}/` - Delete camera (Admin only)
- `PATCH /{id}/status/` - Update camera status
- `GET /zone/{zone}/` - Get cameras by zone

### Alerts (`/api/alerts/`)
- `GET /` - List alerts
- `POST /` - Create alert
- `GET /{id}/` - Get alert details
- `PATCH /{id}/acknowledge/` - Acknowledge/resolve alert
- `GET /active/` - Get active alerts
- `GET /recent/` - Get recent alerts (24h)

### Incidents (`/api/incidents/`)
- `GET /` - List incidents
- `POST /` - Create incident
- `GET /{id}/` - Get incident details
- `PATCH /{id}/status/` - Update incident status
- `PATCH /{id}/assign/` - Assign incident to user
- `GET /my-incidents/` - Get my assigned incidents
- `GET /unassigned/` - Get unassigned incidents

### Surveillance (`/api/surveillance/`)
- `POST /ingest/` - Ingest AI surveillance event
- `GET /events/` - List surveillance events
- `GET /events/{id}/` - Get event details

### Tracking (`/api/tracking/`)
- `POST /ingest/` - Ingest tracking data
- `GET /records/` - List tracking records
- `GET /records/{id}/` - Get tracking record
- `GET /person/{person_id}/path/` - Get person's tracking path

### Mobile/Notifications (`/api/mobile/`)
- `GET /notifications/` - List notifications
- `GET /notifications/me/` - My notifications
- `POST /send-sms/` - Send SMS
- `POST /send-email/` - Send email
- `POST /send-bulk/` - Send bulk notifications

### Dashboard (`/api/dashboard/`)
- `GET /overview/` - Dashboard overview stats
- `GET /alerts-stats/` - Detailed alert statistics
- `GET /incidents-stats/` - Detailed incident statistics
- `GET /cameras-stats/` - Camera statistics
- `GET /recent-activity/` - Recent activity feed

### Feedback (`/api/feedback/`)
- `GET /` - List feedback
- `POST /` - Submit feedback
- `GET /{id}/` - Get feedback details
- `GET /me/` - My feedback
- `GET /stats/` - Feedback statistics (Admin only)

## 🔒 Role-Based Permissions

### ADMIN
- Full access to all endpoints
- User management
- System configuration

### SECURITY_INCHARGE
- View all data
- Assign incidents
- Send notifications
- Acknowledge alerts

### GUARD
- View assigned incidents
- Submit feedback
- View alerts in assigned zones

## 🎯 Key Features

### 1. AI Event Processing
- Receives events from AI detection system via `/api/surveillance/ingest/`
- Automatically creates alerts based on event type and severity
- Auto-generates incidents for high-severity alerts

### 2. Incident Workflow
```
CREATED → ASSIGNED → ACKNOWLEDGED → RESOLVED
```

### 3. Notification System
- SMS via Twilio
- Email via SMTP
- Automatic notifications on:
  - Alert creation (high severity)
  - Incident assignment
  - Status changes

### 4. Person Tracking
- Stores feature vectors for person re-identification
- Tracks person movement across cameras
- Stub implementation for ML integration

### 5. Dashboard Analytics
- Real-time statistics
- Time-series data
- Alert/incident trends
- Camera status monitoring

## 🛠️ Development

### Running Tests
```bash
python manage.py test
```

### Create Migrations
```bash
python manage.py makemigrations
```

### Admin Interface
Access Django admin at: `http://localhost:8000/admin/`

## 📝 Example API Usage

### 1. Register and Login
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "role": "ADMIN"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepass123"
  }'
```

### 2. Create Camera
```bash
curl -X POST http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Entrance Camera",
    "rtsp_url": "rtsp://192.168.1.100:554/stream",
    "location": "Building A - Main Entrance",
    "zone": "Zone A",
    "status": "ONLINE"
  }'
```

### 3. Ingest AI Event
```bash
curl -X POST http://localhost:8000/api/surveillance/ingest/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 1,
    "event_type": "theft_detected",
    "frame_url": "http://storage.example.com/frames/frame123.jpg",
    "ai_data": {
      "confidence": 0.95,
      "bounding_boxes": [[100, 200, 300, 400]],
      "detected_objects": ["person", "bag"]
    }
  }'
```

## 🚀 Production Deployment

### Using Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Environment Variables
Set all sensitive values via environment variables in production.

## 📄 License

Proprietary - Theft Sentinel FYP Project

## 👥 Contributors

FYP Team - AI Powered Anti-Theft System

## 🐛 Known Issues / MVP Limitations

1. **Tracking Service**: Stub implementation - requires ML model integration
2. **Twilio/Email**: Requires valid credentials to function
3. **MongoDB Indexes**: May need optimization for large-scale deployment
4. **File Upload**: Frame storage not implemented (uses URLs)

## 🔜 Future Enhancements

- Real-time WebSocket notifications
- Advanced analytics dashboard
- ML model integration for tracking
- Video stream processing
- Mobile app integration
- Advanced reporting

---

**For support, contact the development team.**

