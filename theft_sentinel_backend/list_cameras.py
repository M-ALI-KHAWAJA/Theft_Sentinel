"""
List all cameras in the database
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cameras.models import Camera

print("=" * 60)
print("ALL CAMERAS IN DATABASE")
print("=" * 60)
print()

cameras = Camera.objects.all()

if not cameras:
    print("⚠️  No cameras found in database")
else:
    print(f"Found {cameras.count()} camera(s):")
    print()
    
    for camera in cameras:
        print(f"📹 {camera.name}")
        print(f"   ID: {camera.id}")
        print(f"   Location: {camera.location}")
        print(f"   Zone: {camera.zone}")
        print(f"   Status: {camera.status}")
        print(f"   RTSP URL: {camera.rtsp_url}")
        print(f"   Created: {camera.created_at}")
        print()

print("=" * 60)

