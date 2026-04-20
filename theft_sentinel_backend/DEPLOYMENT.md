# Deployment Checklist

## Pre-Deployment Setup

### 1. Environment Configuration ✅
- [ ] Copy `.env.example` to `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Set `DEBUG=False` for production
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up MongoDB connection (Atlas or self-hosted)
- [ ] Configure Twilio credentials for SMS
- [ ] Configure SMTP credentials for email
- [ ] Set CORS allowed origins

### 2. Database Setup ✅
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load initial data
# python manage.py loaddata initial_data.json
```

### 3. Static Files ✅
```bash
# Collect static files
python manage.py collectstatic --noinput
```

### 4. Security Checklist ✅
- [ ] Change `SECRET_KEY` from default
- [ ] Set `DEBUG=False`
- [ ] Configure HTTPS/SSL
- [ ] Set secure cookie flags (if using sessions)
- [ ] Configure CORS properly
- [ ] Review Django security settings
- [ ] Set up firewall rules
- [ ] Enable MongoDB authentication

---

## Production Server Setup

### Option 1: Gunicorn + Nginx

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Run Gunicorn
```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - MONGO_URI=${MONGO_URI}
    depends_on:
      - mongodb

  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password

volumes:
  mongodb_data:
```

---

## MongoDB Setup

### Option 1: MongoDB Atlas (Recommended for Production)

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Whitelist IP addresses
4. Create database user
5. Get connection string
6. Update `.env`:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=theft_sentinel
```

### Option 2: Self-Hosted MongoDB

```bash
# Install MongoDB
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create admin user
mongo
> use admin
> db.createUser({
    user: "admin",
    pwd: "secure_password",
    roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

# Update .env
MONGO_URI=mongodb://admin:secure_password@localhost:27017/
```

---

## Twilio Setup (SMS Notifications)

1. Create account at https://www.twilio.com
2. Get phone number
3. Get Account SID and Auth Token
4. Update `.env`:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

---

## Email Setup (SMTP)

### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password
3. Update `.env`:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your.email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your.email@gmail.com
```

### Other SMTP Providers
- **SendGrid**: smtp.sendgrid.net:587
- **Mailgun**: smtp.mailgun.org:587
- **AWS SES**: email-smtp.region.amazonaws.com:587

---

## Monitoring & Logging

### Application Logging
```python
# settings.py - already configured
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

### Sentry Integration (Optional)
```bash
pip install sentry-sdk

# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

---

## Performance Optimization

### 1. Database Indexing
```python
# Already implemented in models with db_index=True
# For additional indexes:
python manage.py dbshell
> db.alerts.createIndex({"timestamp": -1, "status": 1})
> db.incidents.createIndex({"status": 1, "created_at": -1})
```

### 2. Redis Caching (Optional)
```bash
pip install redis django-redis

# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Database Connection Pooling
```python
# For MongoDB Atlas, connection pooling is built-in
# For self-hosted:
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'theft_sentinel',
        'CLIENT': {
            'host': 'mongodb://localhost:27017/',
            'maxPoolSize': 50,
            'minPoolSize': 10,
        }
    }
}
```

---

## Backup Strategy

### 1. MongoDB Backup
```bash
# Manual backup
mongodump --uri="mongodb://user:pass@host:port/theft_sentinel" --out=/backup/$(date +%Y%m%d)

# Automated daily backup (cron)
0 2 * * * mongodump --uri="mongodb://..." --out=/backup/$(date +\%Y\%m\%d)
```

### 2. Application Files Backup
```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

---

## Testing in Production-like Environment

### 1. Staging Environment
```bash
# Set up staging with production-like settings
export DEBUG=False
export DJANGO_SETTINGS_MODULE=config.settings

# Run tests
python manage.py test

# Load testing
pip install locust
locust -f tests/load_test.py
```

### 2. Security Testing
```bash
# Check for vulnerabilities
pip install safety
safety check

# Django security check
python manage.py check --deploy
```

---

## Go-Live Checklist

### Pre-Launch
- [ ] All environment variables configured
- [ ] Database migrated and tested
- [ ] Static files collected and accessible
- [ ] SSL certificate installed
- [ ] Superuser created
- [ ] Test all API endpoints
- [ ] Test notifications (SMS & Email)
- [ ] Review logs for errors
- [ ] Backup strategy in place
- [ ] Monitoring configured

### Launch Day
- [ ] DNS configured
- [ ] Server started
- [ ] Health check endpoint responding
- [ ] API accessible from external
- [ ] Admin panel accessible
- [ ] Create test alert/incident
- [ ] Verify notifications working
- [ ] Monitor logs for errors

### Post-Launch
- [ ] Monitor server resources (CPU, RAM, Disk)
- [ ] Monitor database performance
- [ ] Review application logs
- [ ] Set up alerting for errors
- [ ] Document any issues
- [ ] Train users on the system

---

## Troubleshooting Common Issues

### Issue: Djongo Migration Errors
```bash
# Solution: Clear cache and regenerate
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### Issue: MongoDB Connection Timeout
```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check connection string
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DATABASES)

# Test connection
>>> from pymongo import MongoClient
>>> client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
>>> client.server_info()
```

### Issue: JWT Token Not Working
```bash
# Verify token in request
Authorization: Bearer <token>

# Check token expiry in settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Test token generation
python manage.py shell
>>> from rest_framework_simplejwt.tokens import RefreshToken
>>> from apps.accounts.models import User
>>> user = User.objects.first()
>>> token = RefreshToken.for_user(user)
>>> print(str(token.access_token))
```

### Issue: Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check settings
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# For Nginx, verify location
location /static/ {
    alias /path/to/staticfiles/;
}
```

---

## Support & Maintenance

### Regular Maintenance Tasks
- [ ] Weekly: Review logs for errors
- [ ] Weekly: Check disk space
- [ ] Monthly: Update dependencies (security patches)
- [ ] Monthly: Review and optimize database
- [ ] Quarterly: Full backup test and restore
- [ ] Quarterly: Security audit

### Update Process
```bash
# Backup first
mongodump --uri="..." --out=/backup/pre_update

# Update code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart server
sudo systemctl restart gunicorn
```

---

## Emergency Procedures

### Application Down
1. Check server status: `systemctl status gunicorn`
2. Check logs: `tail -f logs/error.log`
3. Check MongoDB: `systemctl status mongod`
4. Restart if needed: `systemctl restart gunicorn`

### Database Issues
1. Check MongoDB logs: `tail -f /var/log/mongodb/mongod.log`
2. Check disk space: `df -h`
3. Restore from backup if corrupted

### High Load
1. Check resource usage: `top`, `htop`
2. Check slow queries in MongoDB
3. Scale horizontally (add more workers)
4. Enable caching if not already

---

**Deployment completed successfully! 🚀**

For ongoing support, refer to:
- README.md - Full documentation
- API_DOCUMENTATION.md - API reference
- PROJECT_SUMMARY.md - Project overview

