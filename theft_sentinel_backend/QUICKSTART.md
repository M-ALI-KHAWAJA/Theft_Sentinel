# Theft Sentinel - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
cd theft_sentinel_backend
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
```bash
# For development, you can use default MongoDB on localhost
export MONGO_URI=mongodb://localhost:27017/
export MONGO_DB_NAME=theft_sentinel
export SECRET_KEY=dev-secret-key-change-in-production
```

Or create a `.env` file (recommended):
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=theft_sentinel
```

### Step 3: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Superuser
```bash
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

### Step 5: Run Server
```bash
python manage.py runserver
```

Server will start at `http://localhost:8000/`

---

## 🧪 Test the API

### 1. Access Admin Panel
Visit: `http://localhost:8000/admin/`
Login with your superuser credentials

### 2. Get API Token
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Save the `access` token from the response.

### 3. Create a Camera
```bash
curl -X POST http://localhost:8000/api/cameras/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Camera",
    "rtsp_url": "rtsp://192.168.1.100:554/stream",
    "location": "Main Entrance",
    "zone": "Zone A",
    "status": "ONLINE"
  }'
```

### 4. Test Dashboard
```bash
curl -X GET http://localhost:8000/api/dashboard/overview/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📝 Common Commands

### Create App
```bash
python manage.py startapp app_name
```

### Make Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Run Server
```bash
python manage.py runserver
# Or on specific port
python manage.py runserver 8080
```

### Run Tests
```bash
python manage.py test
```

### Collect Static Files
```bash
python manage.py collectstatic
```

---

## 🔧 Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `mongod --version`
- Check connection string in `.env`
- For MongoDB Atlas, use full connection string with credentials

### Djongo Migration Errors
- Delete `__pycache__` folders
- Delete migration files (keep `__init__.py`)
- Run `makemigrations` and `migrate` again

### Import Errors
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

### JWT Token Expired
- Refresh token using `/api/auth/refresh/` endpoint
- Or login again to get new tokens

---

## 📦 Project Structure Quick Reference

```
theft_sentinel_backend/
├── config/                  # Project settings
│   ├── settings.py         # Main configuration
│   └── urls.py             # Root URL routing
├── apps/
│   ├── accounts/           # Authentication & Users
│   ├── cameras/            # Camera management
│   ├── alerts/             # Alert system
│   ├── incidents/          # Incident workflow
│   ├── surveillance/       # AI event processing
│   ├── tracking/           # Person tracking
│   ├── mobile/             # Notifications
│   ├── dashboard/          # Analytics
│   ├── feedback/           # User feedback
│   └── personnel/          # Staff profiles
├── manage.py               # Django management
├── requirements.txt        # Dependencies
└── README.md              # Full documentation
```

---

## 🎯 Next Steps

1. **Configure Twilio** (for SMS):
   - Get account from twilio.com
   - Add credentials to `.env`

2. **Configure Email** (for notifications):
   - Use Gmail with App Password
   - Add to `.env`

3. **Set up MongoDB Atlas** (for production):
   - Create cluster at mongodb.com/atlas
   - Get connection string
   - Update `MONGO_URI`

4. **Integrate AI System**:
   - Use `/api/surveillance/ingest/` endpoint
   - Send detected events with confidence scores

5. **Deploy**:
   - Use Gunicorn for production
   - Set up Nginx as reverse proxy
   - Use environment variables for secrets

---

For detailed API documentation, see `API_DOCUMENTATION.md`
For full setup guide, see `README.md`

