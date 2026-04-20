# MongoDB Atlas Configuration Guide

## ✅ Status: Connected Successfully!

Your MongoDB Atlas database is now configured and connected.

---

## 🔐 Security Setup

### Current Configuration:
- **Database**: MongoDB Atlas (Cloud)
- **Database Name**: `theft_sentinel`
- **Connection**: Secured via `.env` file
- **Credentials**: Stored in `.env` (never commit this file!)

### Important Security Notes:

1. ✅ **Credentials are secured** - The `.env` file contains your database password
2. ✅ **Git protection** - `.env` is in `.gitignore` and won't be committed
3. ⚠️  **Never share** - Don't share your `.env` file or commit it to version control
4. ⚠️  **Change in production** - Use different credentials for production

---

## 📁 Configuration Files

### `.env` file structure:
```env
# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://admin:YOUR_PASSWORD@cluster0.hvpnb5y.mongodb.net/?appName=Cluster0
MONGO_DB_NAME=theft_sentinel
```

### How it works:
1. Django settings loads credentials from `.env` using `python-decouple`
2. MongoDB connection is established via `config/mongodb.py`
3. All models can access MongoDB through the `mongodb` utility

---

## 🚀 Usage in Your Code

### Option 1: Using the MongoDB Utility (Recommended)

```python
from config.mongodb import get_db, get_collection

# Get database
db = get_db()

# Get a collection
users_collection = get_collection('users')

# Insert data
users_collection.insert_one({
    'username': 'john_doe',
    'email': 'john@example.com'
})

# Find data
user = users_collection.find_one({'username': 'john_doe'})
```

### Option 2: Direct Access from Settings

```python
from django.conf import settings
from pymongo import MongoClient

# Access MongoDB settings
uri = settings.MONGODB_URI
db_name = settings.MONGODB_NAME

# Create connection
client = MongoClient(uri)
db = client[db_name]
```

---

## 🗄️ Collections Structure

Your Django models use **SQLite** for Django's auth system, while **MongoDB** is available for:

- Real-time surveillance data
- Large-scale tracking records
- Complex JSON documents
- High-volume event logs

### Recommended Collections:

```
theft_sentinel/
├── surveillance_events/    - AI detection events
├── tracking_data/          - Person tracking vectors
├── alert_metadata/         - Additional alert data
├── activity_logs/          - System activity logs
└── analytics_cache/        - Cached analytics data
```

---

## 🧪 Testing the Connection

Run this test to verify MongoDB is working:

```bash
python manage.py shell
```

Then in the Python shell:
```python
from config.mongodb import get_db

db = get_db()
print(f"Connected to: {db.name}")

# List collections
print("Collections:", db.list_collection_names())

# Test insert
test_collection = db['test']
result = test_collection.insert_one({'test': 'data'})
print(f"Inserted ID: {result.inserted_id}")

# Clean up
test_collection.delete_one({'test': 'data'})
```

---

## 📊 MongoDB Atlas Dashboard

Access your database at: https://cloud.mongodb.com/

Features available:
- Real-time monitoring
- Query performance insights
- Data browser
- Backup configuration
- Security settings

---

## 🔧 Configuration Options

### Update MongoDB URI:
Edit `.env` file:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### Change Database Name:
Edit `.env` file:
```env
MONGO_DB_NAME=your_database_name
```

### Add IP Whitelist (MongoDB Atlas):
1. Go to MongoDB Atlas dashboard
2. Network Access → Add IP Address
3. Add your server's IP or use `0.0.0.0/0` for development (not recommended for production)

---

## 🚨 Troubleshooting

### Connection Failed?

1. **Check credentials**: Verify username and password in `.env`
2. **IP Whitelist**: Add your IP in MongoDB Atlas → Network Access
3. **Firewall**: Check if port 27017 is open
4. **Internet**: Ensure you have internet connection

### Test connection:
```bash
python -c "from config.mongodb import get_db; print('✅ Connected!' if get_db() else '❌ Failed')"
```

---

## 📝 Best Practices

### Development:
- ✅ Use `.env` for local configuration
- ✅ Different database for development/testing
- ✅ Enable debug logging

### Production:
- ⚠️  Use environment variables (not .env file)
- ⚠️  Strong passwords (use password manager)
- ⚠️  IP whitelist (specific IPs only)
- ⚠️  Enable MongoDB authentication
- ⚠️  Regular backups
- ⚠️  Monitor connection pool
- ⚠️  Use read/write concerns

---

## 🔄 Migration from SQLite to MongoDB

If you want to migrate existing data:

```python
from django.core.management.base import BaseCommand
from config.mongodb import get_collection
from apps.your_app.models import YourModel

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        collection = get_collection('your_collection')
        
        for obj in YourModel.objects.all():
            collection.insert_one({
                'id': obj.id,
                'field': obj.field,
                # ... more fields
            })
```

---

## 📞 Support

- **MongoDB Docs**: https://docs.mongodb.com/
- **PyMongo Docs**: https://pymongo.readthedocs.io/
- **Django + MongoDB**: See `config/mongodb.py` for implementation

---

**Status**: ✅ MongoDB Atlas is connected and ready to use!

