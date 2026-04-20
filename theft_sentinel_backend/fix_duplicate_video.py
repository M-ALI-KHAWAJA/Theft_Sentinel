"""
Fix duplicate /video in camera URLs
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.cameras.models import Camera

print("=" * 60)
print("FIXING CAMERA URLs")
print("=" * 60)
print()

cameras = Camera.objects.all()
fixed_count = 0

for camera in cameras:
    old_url = camera.rtsp_url
    needs_fix = False
    
    # Fix duplicate /video
    if '/video/video' in camera.rtsp_url:
        camera.rtsp_url = camera.rtsp_url.replace('/video/video', '/video')
        needs_fix = True
    
    # Add /video if missing (IP Webcam format)
    elif camera.rtsp_url.startswith('http://') and not camera.rtsp_url.endswith('/video'):
        if ':8080' in camera.rtsp_url or ':4747' in camera.rtsp_url:
            camera.rtsp_url = camera.rtsp_url.rstrip('/') + '/video'
            needs_fix = True
    
    if needs_fix:
        camera.save()
        print(f"📹 {camera.name}")
        print(f"   ❌ OLD: {old_url}")
        print(f"   ✅ NEW: {camera.rtsp_url}")
        print()
        fixed_count += 1
    else:
        print(f"📹 {camera.name}")
        print(f"   ✅ Already correct: {camera.rtsp_url}")
        print()

print("=" * 60)
if fixed_count > 0:
    print(f"✅ Fixed {fixed_count} camera(s)")
else:
    print("✅ All cameras already have correct URLs")
print()
print("Next steps:")
print("1. python test_camera_rtsp.py  - Test cameras")
print("2. Restart Django server")
print("3. Test AI monitoring in frontend")
print("=" * 60)

