"""
Camera Views
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse, JsonResponse
import cv2
import threading
import time
import requests

from .models import Camera
from .serializers import CameraSerializer, CameraCreateSerializer, CameraStatusUpdateSerializer
from apps.accounts.permissions import CanManageCameras, CanViewCameraFeeds


class CameraListCreateView(generics.ListCreateAPIView):
    """
    List all cameras or create new
    All authenticated users can view cameras
    Only Admin can add/edit/delete cameras
    """
    queryset = Camera.objects.all()
    permission_classes = [IsAuthenticated, CanManageCameras]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CameraCreateSerializer
        return CameraSerializer
    
    def get_queryset(self):
        queryset = Camera.objects.all()
        
        # Filter by zone
        zone = self.request.query_params.get('zone', None)
        if zone:
            queryset = queryset.filter(zone=zone)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class CameraDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete camera
    All authenticated users can view camera details
    Only Admin can update/delete cameras
    """
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated, CanManageCameras]


class CameraStatusUpdateView(views.APIView):
    """
    Update camera status
    Only Admin can update camera status
    """
    permission_classes = [IsAuthenticated, CanManageCameras]
    
    def patch(self, request, pk):
        try:
            camera = Camera.objects.get(pk=pk)
        except Camera.DoesNotExist:
            return Response(
                {'error': 'Camera not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CameraStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            camera.status = serializer.validated_data['status']
            camera.save()
            return Response(CameraSerializer(camera).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CamerasByZoneView(generics.ListAPIView):
    """
    Get all cameras in a specific zone
    All authenticated users can view cameras
    """
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated, CanViewCameraFeeds]
    
    def get_queryset(self):
        zone = self.kwargs.get('zone')
        return Camera.objects.filter(zone=zone).order_by('name')


class CameraStreamURLView(views.APIView):
    """
    Get direct camera stream URL
    All authenticated users can view camera feeds
    (Admin, Security In-Charge, Security Guard)
    """
    permission_classes = [IsAuthenticated, CanViewCameraFeeds]
    
    def get(self, request, pk):
        try:
            camera = Camera.objects.get(pk=pk)
        except Camera.DoesNotExist:
            return JsonResponse(
                {'error': 'Camera not found'},
                status=404
            )
        
        # Determine the best stream URL
        stream_url = camera.rtsp_url
        
        # For HTTP streams, add /video endpoint
        if stream_url.startswith('http://') or stream_url.startswith('https://'):
            if not stream_url.endswith('/video'):
                stream_url = stream_url.rstrip('/') + '/video'
        
        return JsonResponse({
            'camera_id': str(camera.id),
            'camera_name': camera.name,
            'stream_url': stream_url,
            'status': camera.status,
            'location': camera.location,
            'zone': camera.zone,
            'stream_type': 'http' if stream_url.startswith('http') else 'rtsp'
        })


class CameraFeedView(views.APIView):
    """
    Stream camera feed from RTSP URL
    All authenticated users can view real-time camera feeds
    (Admin, Security In-Charge, Security Guard)
    """
    permission_classes = []  # Allow unauthenticated for img tag, but check token manually
    
    def get(self, request, pk):
        # Optional: Check for token in query parameter for production security
        # token = request.GET.get('token')
        # if token:
        #     # Validate JWT token here
        #     pass
        
        try:
            camera = Camera.objects.get(pk=pk)
        except Camera.DoesNotExist:
            return JsonResponse(
                {'error': 'Camera not found'},
                status=404
            )
        
        # Check if camera is online
        if camera.status != 'ONLINE':
            return JsonResponse(
                {'error': 'Camera is offline', 'status': camera.status},
                status=503
            )
        
        # Check if we should use direct proxy mode
        use_proxy = request.GET.get('proxy', 'false').lower() == 'true'
        
        # For HTTP/HTTPS streams, redirect directly to camera (zero latency)
        if not use_proxy and (camera.rtsp_url.startswith('http://') or camera.rtsp_url.startswith('https://')):
            # Return direct camera URL for zero-latency streaming
            camera_url = camera.rtsp_url.rstrip('/') + '/video'
            print(f"[Camera Feed] Redirecting to direct stream: {camera_url}")
            
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(camera_url)
        
        def generate_frames():
            """Generate frames from RTSP/HTTP stream"""
            stream_url = camera.rtsp_url
            
            # Check if it's an HTTP/HTTPS stream (like IP Webcam)
            if stream_url.startswith('http://') or stream_url.startswith('https://'):
                # Try direct HTTP streaming first (for IP Webcam, DroidCam, etc.)
                try:
                    # Common endpoints for mobile camera apps
                    possible_endpoints = [
                        '/video',
                        '/videofeed',
                        '/shot.jpg',
                        '/photoaf.jpg',
                        ''  # Try base URL
                    ]
                    
                    for endpoint in possible_endpoints:
                        try:
                            test_url = stream_url.rstrip('/') + endpoint
                            # Optimize connection for low latency
                            response = requests.get(
                                test_url, 
                                stream=True, 
                                timeout=5,
                                headers={
                                    'Connection': 'keep-alive',
                                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                                    'Pragma': 'no-cache'
                                }
                            )
                            
                            if response.status_code == 200:
                                content_type = response.headers.get('Content-Type', '')
                                
                                # Check if it's MJPEG stream (priority)
                                if 'multipart' in content_type:
                                    print(f"[Camera Feed] Streaming MJPEG from {test_url}")
                                    # Proxy the MJPEG stream directly with optimizations
                                    try:
                                        # Use larger chunk size for better performance
                                        # Disable buffering to reduce latency
                                        for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                                            if chunk:
                                                yield chunk
                                    except Exception as e:
                                        print(f"[Camera Feed] Stream interrupted: {str(e)}")
                                    return
                                    
                        except Exception as e:
                            continue
                    
                    # If no MJPEG stream found, try single image endpoints
                    for endpoint in possible_endpoints:
                        try:
                            test_url = stream_url.rstrip('/') + endpoint
                            response = requests.get(test_url, timeout=5)
                            
                            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                                print(f"[Camera Feed] Using snapshot mode from {test_url}")
                                # Single image endpoint - refresh periodically
                                while True:
                                    try:
                                        img_response = requests.get(test_url, timeout=5)
                                        if img_response.status_code == 200:
                                            yield (b'--frame\r\n'
                                                   b'Content-Type: image/jpeg\r\n\r\n' + 
                                                   img_response.content + b'\r\n')
                                            time.sleep(0.1)  # 10 FPS
                                        else:
                                            break
                                    except:
                                        break
                                return
                        except:
                            continue
                    
                    # If HTTP streaming failed, fall back to OpenCV
                    print(f"[Camera Feed] HTTP streaming failed, trying OpenCV for {stream_url}")
                    
                except Exception as e:
                    print(f"[Camera Feed] HTTP stream error: {str(e)}")
            
            # Fall back to OpenCV for RTSP or if HTTP failed
            cap = None
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    # Open video stream (supports RTSP, HTTP, RTMP, etc.)
                    cap = cv2.VideoCapture(stream_url)
                    
                    if not cap.isOpened():
                        retry_count += 1
                        time.sleep(1)
                        continue
                    
                    # Optimize for low latency
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
                    cap.set(cv2.CAP_PROP_FPS, 30)  # Set FPS
                    
                    # For RTSP streams, reduce latency
                    if stream_url.startswith('rtsp://'):
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    
                    print(f"[Camera Feed] OpenCV connected to {stream_url}")
                    
                    frame_count = 0
                    while True:
                        success, frame = cap.read()
                        
                        if not success:
                            # Try to grab multiple frames to clear buffer (reduces latency)
                            for _ in range(5):
                                cap.grab()
                            continue
                        
                        frame_count += 1
                        
                        # Skip frames if buffer is building up (optional - reduces latency)
                        # Uncomment to skip every other frame for lower latency
                        # if frame_count % 2 == 0:
                        #     continue
                        
                        # Encode frame as JPEG with optimized quality for speed
                        # Lower quality = faster encoding = less latency
                        ret, buffer = cv2.imencode('.jpg', frame, [
                            cv2.IMWRITE_JPEG_QUALITY, 75,  # Reduced from 85 for speed
                            cv2.IMWRITE_JPEG_OPTIMIZE, 1   # Enable optimization
                        ])
                        
                        if not ret:
                            continue
                        
                        # Yield frame in multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    
                except Exception as e:
                    print(f"[Camera Feed Error] Camera: {camera.name}, URL: {stream_url}, Error: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(1)
                
                finally:
                    if cap is not None:
                        cap.release()
            
            # If all retries failed
            yield (b'--frame\r\n'
                   b'Content-Type: text/plain\r\n\r\n'
                   b'Failed to connect to camera stream. Please check camera URL and network connectivity.\r\n')
        
        return StreamingHttpResponse(
            generate_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )

