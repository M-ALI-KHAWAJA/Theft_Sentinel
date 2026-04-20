# Fix Export Endpoint 404 Error

## Problem
The export endpoints (`/api/dashboard/export-incidents/`) are returning 404 errors even after code changes.

## Solution Steps

### Step 1: Stop Django Server Completely
1. Go to the terminal where Django is running
2. Press `Ctrl+C` to stop the server
3. Make sure it's completely stopped (you should see the command prompt)

### Step 2: Clear Python Cache Files
Run these commands to clear cached Python files:

```powershell
# Navigate to the backend directory
cd Theft_Sentinel-main\Theft_Sentinel-main\theft_sentinel_backend

# Remove all __pycache__ directories
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force

# Remove .pyc files
Get-ChildItem -Path . -Filter *.pyc -Recurse -File | Remove-Item -Force
```

### Step 3: Verify the Code Files
Make sure these files exist and have the correct content:

1. **Check `apps/dashboard/views.py`** - Should contain `IncidentReportExportView` class (around line 552)
2. **Check `apps/dashboard/urls.py`** - Should import and include `IncidentReportExportView` (line 13 and 25)

### Step 4: Restart Django Server
```powershell
cd Theft_Sentinel-main\Theft_Sentinel-main\theft_sentinel_backend
python manage.py runserver
```

### Step 5: Check for Errors
When the server starts, look for any import errors in the console. You should see:
- No errors about `IncidentReportExportView`
- Server starting successfully on port 8000

### Step 6: Test the Endpoint
1. Make sure you're logged in as Admin or Security Incharge
2. Try accessing the endpoint directly in browser (while logged in):
   ```
   http://localhost:8000/api/dashboard/export-incidents/?format=csv&days=30&period=daily
   ```
3. You should get a CSV file download, NOT a 404 error

### Step 7: If Still Getting 404

#### Check Django URL Patterns
Add this temporary view to test:

```python
# In apps/dashboard/views.py, add at the end:
class TestExportView(views.APIView):
    def get(self, request):
        return Response({'message': 'Export endpoint is working!'}, status=status.HTTP_200_OK)
```

And in `apps/dashboard/urls.py`:
```python
path('test-export/', TestExportView.as_view(), name='test_export'),
```

Then test: `http://localhost:8000/api/dashboard/test-export/`

If this works but export-incidents doesn't, there's an issue with the IncidentReportExportView class.

#### Check Server Logs
Look at the Django server console when you make the request. You should see:
```
GET /api/dashboard/export-incidents/?format=csv&days=30&period=daily HTTP/1.1" 200
```

If you see 404, the URL isn't registered.

#### Verify URL Registration
Check that `apps/dashboard/urls.py` is included in `config/urls.py`:
```python
path('api/dashboard/', include('apps.dashboard.urls')),
```

## Common Issues

1. **Server not restarted** - Most common cause
2. **Python cache files** - Old cached code being used
3. **Import errors** - Check server console for Python errors
4. **Wrong virtual environment** - Make sure you're using the correct Python environment
5. **Port conflict** - Server might be running on a different port

## Verification

After following all steps, the export should work. If it doesn't, check:
- Django server console for errors
- Browser console for network errors
- Authentication status (must be logged in as Admin or Security Incharge)

