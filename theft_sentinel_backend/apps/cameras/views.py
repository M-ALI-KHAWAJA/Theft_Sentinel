"""
Camera Views
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse, JsonResponse
import logging
import requests

from .stream_manager import stream_manager

logger = logging.getLogger(__name__)

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

        # Branch scoping (single DB, tenant isolation)
        user_branch = getattr(self.request.user, "branch", None)
        if getattr(self.request.user, "role", None) != "SUPER_ADMIN" and user_branch is not None:
            queryset = queryset.filter(branch=user_branch)
        
        # Filter by zone
        zone = self.request.query_params.get('zone', None)
        if zone:
            queryset = queryset.filter(zone=zone)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # Ensure camera is linked to creator's branch (Super Admin may omit)
        user_branch = getattr(self.request.user, "branch", None)
        if getattr(self.request.user, "role", None) != "SUPER_ADMIN" and user_branch is not None:
            serializer.save(branch=user_branch)
            return
        serializer.save()


class CameraDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete camera
    All authenticated users can view camera details
    Only Admin can update/delete cameras
    """
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated, CanManageCameras]

    def get_queryset(self):
        qs = Camera.objects.all()
        user_branch = getattr(self.request.user, "branch", None)
        if getattr(self.request.user, "role", None) != "SUPER_ADMIN" and user_branch is not None:
            qs = qs.filter(branch=user_branch)
        return qs


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
    Stream MJPEG camera feed using a SINGLE persistent RTSP connection.

    Architecture:
        RTSP Camera
            ↓
        CameraStreamManager (one VideoCapture per camera, daemon reader thread)
            ↓
        Shared latest-frame cache  (thread-safe)
            ↓
        Multiple MJPEG clients  ← this view

    No new cv2.VideoCapture is ever opened per HTTP request.  All clients
    for the same camera read from the same shared frame buffer.
    """
    permission_classes = []  # Allow unauthenticated for <img> tags; add JWT check if needed

    def get(self, request, pk):
        try:
            camera = Camera.objects.get(pk=pk)
        except Camera.DoesNotExist:
            return JsonResponse({'error': 'Camera not found'}, status=404)

        # Camera must be marked ONLINE before we attempt streaming
        if camera.status != 'ONLINE':
            logger.warning(
                "[CameraFeedView] Camera %s is %s — rejecting stream request",
                camera.name, camera.status,
            )
            return JsonResponse(
                {'error': 'Camera is offline', 'status': camera.status},
                status=503,
            )

        # HTTP/HTTPS cameras (IP Webcam, DroidCam) — proxy the native MJPEG
        # stream directly without touching cv2.VideoCapture at all.
        rtsp_url = camera.rtsp_url
        if rtsp_url.startswith('http://') or rtsp_url.startswith('https://'):
            return self._proxy_http_stream(camera, rtsp_url, request)

        # RTSP cameras — use the singleton stream manager
        camera_id = str(camera.id)
        logger.info(
            "[CameraFeedView] Client connected for camera %s (id=%s)",
            camera.name, camera_id,
        )

        return StreamingHttpResponse(
            stream_manager.mjpeg_frame_generator(camera_id, rtsp_url),
            content_type='multipart/x-mixed-replace; boundary=frame',
        )

    # ── HTTP/HTTPS stream proxy ───────────────────────────────────────────────

    def _proxy_http_stream(self, camera, stream_url, request):
        """
        Proxy a native HTTP MJPEG stream (IP Webcam / DroidCam) directly to
        the browser — zero re-encoding overhead.
        """
        possible_endpoints = ['/video', '/videofeed', '/shot.jpg', '/photoaf.jpg', '']

        for endpoint in possible_endpoints:
            test_url = stream_url.rstrip('/') + endpoint
            try:
                resp = requests.get(
                    test_url,
                    stream=True,
                    timeout=5,
                    headers={
                        'Connection': 'keep-alive',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                    },
                )
                if resp.status_code != 200:
                    continue

                content_type = resp.headers.get('Content-Type', '')

                # Native MJPEG — pass bytes straight through
                if 'multipart' in content_type:
                    logger.info(
                        "[CameraFeedView] Proxying native MJPEG from %s for camera %s",
                        test_url, camera.name,
                    )

                    def _proxy_gen(response=resp):
                        try:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    yield chunk
                        except Exception as exc:
                            logger.warning(
                                "[CameraFeedView] HTTP proxy interrupted for camera %s: %s",
                                camera.name, exc,
                            )

                    return StreamingHttpResponse(
                        _proxy_gen(),
                        content_type=content_type,
                    )

            except requests.exceptions.RequestException:
                continue

        # Fallback — redirect browser directly to the camera URL
        from django.http import HttpResponseRedirect
        fallback_url = stream_url.rstrip('/') + '/video'
        logger.warning(
            "[CameraFeedView] All HTTP endpoints failed for camera %s — redirecting to %s",
            camera.name, fallback_url,
        )
        return HttpResponseRedirect(fallback_url)

