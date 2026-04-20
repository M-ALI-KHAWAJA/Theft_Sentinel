"""
Fix camera URLs - Remove /video since IP Webcam shows feed on base URL
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cameras.models import Camera

print("=" * 60)
print("FIXING CAMERA URLs - REMOVING /video")
print("=" * 60)
print()

# Target URLs based on your cameras
camera_fixes = {
    '6924b8128134c437308926fa': {  # Ali Mobile
        'name': 'Ali Mobile',
        'correct_url': 'http://192.168.10.33:8080'
    },
    '69248762f00ce64af203fabb': {  # Mohid Mobile
        'name': 'Mohid Mobile', 
        'correct_url': 'http://192.168.10.2:8080'
    }
}

fixed_count = 0

for camera_id, fix_data in camera_fixes.items():
    try:
        camera = Camera.objects.get(id=camera_id)
        old_url = camera.rtsp_url
        
        print(f"📹 {camera.name}")
        print(f"   ID: {camera.id}")
        print(f"   ❌ OLD: {old_url}")
        
        # Set correct URL (without /video)
        camera.rtsp_url = fix_data['correct_url']
        camera.status = 'ONLINE'
        camera.save()
        
        print(f"   ✅ NEW: {camera.rtsp_url}")
        print()
        fixed_count += 1
        
    except Camera.DoesNotExist:
        print(f"⚠️  Camera '{fix_data['name']}' not found")
        print()

print("=" * 60)
print(f"✅ Fixed {fixed_count} camera(s)")
print()
print("URLs are now set to base IP Webcam URLs (no /video)")
print()
print("Next steps:")
print("1. python test_camera_rtsp.py  - Test cameras")
print("2. Restart Django server (Ctrl+C then python manage.py runserver)")
print("3. Refresh browser (Ctrl+Shift+R) and test again")
print("=" * 60)

