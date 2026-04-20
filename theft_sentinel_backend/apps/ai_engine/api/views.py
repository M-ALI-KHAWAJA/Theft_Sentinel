"""
AI Engine API Views
Provides endpoints for AI processing without modifying existing code
"""
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging
import time

from apps.ai_engine.services.ai_service import ai_service
from apps.ai_engine.services.inference_runner import InferenceRunner
from apps.ai_engine.utils.frame_utils import (
    decode_base64_frame,
    capture_frame_from_rtsp,
    validate_frame,
)
from apps.ai_engine.models import AIInference, DetectionTrack
from apps.cameras.models import Camera

# Import existing alert/incident logic (DO NOT MODIFY THEM)
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertCreateSerializer
from apps.incidents.models import Incident

from .serializers import (
    FrameAnalysisRequestSerializer,
    CameraProcessRequestSerializer,
    AnalysisResponseSerializer,
    ModelInfoSerializer,
    AIInferenceSerializer,
)

logger = logging.getLogger(__name__)


class AnalyzeFrameView(views.APIView):
    """
    POST /api/ai/analyze-frame/
    
    Analyze a single frame for theft detection
    Accepts base64 encoded image
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate request
        serializer = FrameAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Check AI service ready
        if not ai_service.is_ready():
            return Response(
                {'error': 'AI service not initialized. Models may still be loading.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Decode frame
        frame = decode_base64_frame(data['frame'])
        if frame is None:
            return Response(
                {'error': 'Failed to decode frame from base64'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate frame
        is_valid, error_msg = validate_frame(frame)
        if not is_valid:
            return Response(
                {'error': f'Invalid frame: {error_msg}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get camera if provided
        camera = None
        camera_id = data.get('camera_id')
        if camera_id:
            try:
                camera = Camera.objects.get(pk=camera_id)
            except Camera.DoesNotExist:
                return Response(
                    {'error': f'Camera not found: {camera_id}'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Run inference
        try:
            runner = InferenceRunner()
            result = runner.process_frame(frame, camera_id=camera_id)
            
            # Handle theft detection
            alert_created = False
            alert_id = None
            inference_id = None
            
            if result['classification'] == 'theft' and data.get('create_alert_on_theft', True):
                if camera:
                    # Call existing alert creation logic (DO NOT MODIFY IT)
                    alert = self._create_alert_for_theft(camera, result, request.user)
                    if alert:
                        alert_created = True
                        alert_id = str(alert.id)
                        logger.info(f"🚨 Theft alert created: {alert_id}")
            
            # Save to database if requested
            if data.get('save_to_db', True):
                inference = self._save_inference(camera, result, alert_id)
                if inference:
                    inference_id = str(inference.id)
            
            # Build response with flattened metadata for frontend
            response_data = {
                # AI Results
                'classification': result['classification'],
                'confidence': result['confidence'],
                
                # Counts (flattened from frame_metadata)
                'persons': result['frame_metadata'].get('num_persons', 0),
                'objects': result['frame_metadata'].get('num_detections', 0),
                'tracks': result['frame_metadata'].get('num_tracks', 0),
                
                # Performance
                'processing_time_ms': result.get('processing_time_ms', 0),
                
                # Camera Info (if available)
                'camera_name': camera.name if camera else None,
                'camera_location': camera.location if camera else None,
                'camera_id': str(camera.id) if camera else camera_id,
                
                # Alert Status
                'alert_created': alert_created,
                'alert_id': alert_id,
                'inference_id': inference_id,
                
                # Detailed Data (optional)
                'detections': result.get('detections', []),
                'poses': result.get('poses', []),
                'tracks_data': result.get('tracks', []),
                'suspicious_tracks': result.get('suspicious_tracks', []),
                'frame_metadata': result.get('frame_metadata', {}),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error processing frame: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_alert_for_theft(self, camera, result, user):
        """
        Create alert using EXISTING alert creation logic
        DO NOT MODIFY - only call existing code
        """
        try:
            # Prepare metadata
            metadata = {
                'confidence': result['confidence'],
                'suspicious_tracks': result.get('suspicious_tracks', []),
                'num_detections': result['frame_metadata'].get('num_detections', 0),
                'num_persons': result['frame_metadata'].get('num_persons', 0),
                'detected_by': 'AI_ENGINE',
                'detection_timestamp': timezone.now().isoformat(),
            }
            
            # Use existing AlertCreateSerializer (DO NOT MODIFY)
            alert_data = {
                'camera_id': camera.id,
                'alert_type': 'THEFT_DETECTED',
                'severity': 'HIGH' if result['confidence'] > 0.7 else 'MEDIUM',
                'metadata': metadata,
            }
            
            alert_serializer = AlertCreateSerializer(data=alert_data)
            if alert_serializer.is_valid():
                alert = alert_serializer.save()
                
                # Optionally create incident (using existing logic)
                # Incident.objects.create(alert_id=alert, status='CREATED')
                
                return alert
            else:
                logger.error(f"Failed to create alert: {alert_serializer.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}", exc_info=True)
            return None
    
    def _save_inference(self, camera, result, alert_id=None):
        """Save inference result to database"""
        try:
            alert = None
            if alert_id:
                try:
                    alert = Alert.objects.get(pk=alert_id)
                except Alert.DoesNotExist:
                    pass
            
            inference = AIInference.objects.create(
                camera_id=camera,
                detections=result['detections'],
                poses=result['poses'],
                tracks=result['tracks'],
                classification=result['classification'],
                confidence=result['confidence'],
                frame_metadata=result['frame_metadata'],
                processing_time_ms=result['processing_time_ms'],
                alert=alert,
            )
            
            return inference
            
        except Exception as e:
            logger.error(f"Error saving inference: {str(e)}", exc_info=True)
            return None


class ProcessCameraView(views.APIView):
    """
    POST /api/ai/process-camera/
    
    Capture frame from camera RTSP stream and analyze it
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate request
        serializer = CameraProcessRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Check AI service ready
        if not ai_service.is_ready():
            return Response(
                {'error': 'AI service not initialized'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Get camera
        camera_id = data['camera_id']
        try:
            camera = Camera.objects.get(pk=camera_id)
        except Camera.DoesNotExist:
            return Response(
                {'error': f'Camera not found: {camera_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Capture frame from RTSP
        logger.info(f"Capturing frame from camera {camera.name} (ID: {camera_id})")
        frame = capture_frame_from_rtsp(camera.rtsp_url)
        if frame is None:
            logger.error(f"Failed to capture frame from camera {camera.name}")
            return Response(
                {
                    'error': 'Failed to capture frame from camera',
                    'details': {
                        'camera_name': camera.name,
                        'camera_id': str(camera_id),
                        'possible_causes': [
                            'Camera is offline or unreachable',
                            'RTSP URL is invalid or incorrect',
                            'Network connectivity issue',
                            'Camera credentials are wrong',
                            'Camera is not streaming',
                        ],
                        'rtsp_url_preview': camera.rtsp_url[:30] + '...' if len(camera.rtsp_url) > 30 else camera.rtsp_url
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Validate frame
        is_valid, error_msg = validate_frame(frame)
        if not is_valid:
            return Response(
                {'error': f'Invalid frame: {error_msg}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Run inference
        try:
            runner = InferenceRunner()
            result = runner.process_frame(frame, camera_id=str(camera.id))
            
            # Handle theft detection
            alert_created = False
            alert_id = None
            inference_id = None
            
            if result['classification'] == 'theft' and data.get('create_alert_on_theft', True):
                alert = self._create_alert_for_theft(camera, result, request.user)
                if alert:
                    alert_created = True
                    alert_id = str(alert.id)
                    logger.info(f"🚨 Theft alert created for camera {camera.name}: {alert_id}")
            
            # Save to database if requested
            if data.get('save_to_db', True):
                inference = self._save_inference(camera, result, alert_id)
                if inference:
                    inference_id = str(inference.id)
            
            # Build response with flattened metadata for frontend
            response_data = {
                # AI Results
                'classification': result['classification'],
                'confidence': result['confidence'],
                
                # Counts (flattened from frame_metadata)
                'persons': result['frame_metadata'].get('num_persons', 0),
                'objects': result['frame_metadata'].get('num_detections', 0),
                'tracks': result['frame_metadata'].get('num_tracks', 0),
                
                # Performance
                'processing_time_ms': result.get('processing_time_ms', 0),
                
                # Camera Info
                'camera_name': camera.name,
                'camera_location': camera.location,
                'camera_id': str(camera.id),
                
                # Alert Status
                'alert_created': alert_created,
                'alert_id': alert_id,
                'inference_id': inference_id,
                
                # Detailed Data (optional)
                'detections': result.get('detections', []),
                'poses': result.get('poses', []),
                'tracks_data': result.get('tracks', []),
                'suspicious_tracks': result.get('suspicious_tracks', []),
                'frame_metadata': result.get('frame_metadata', {}),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing camera: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error processing camera: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_alert_for_theft(self, camera, result, user):
        """Same as AnalyzeFrameView"""
        try:
            metadata = {
                'confidence': result['confidence'],
                'suspicious_tracks': result.get('suspicious_tracks', []),
                'num_detections': result['frame_metadata'].get('num_detections', 0),
                'num_persons': result['frame_metadata'].get('num_persons', 0),
                'detected_by': 'AI_ENGINE',
                'detection_timestamp': timezone.now().isoformat(),
            }
            
            alert_data = {
                'camera_id': camera.id,
                'alert_type': 'THEFT_DETECTED',
                'severity': 'HIGH' if result['confidence'] > 0.7 else 'MEDIUM',
                'metadata': metadata,
            }
            
            alert_serializer = AlertCreateSerializer(data=alert_data)
            if alert_serializer.is_valid():
                alert = alert_serializer.save()
                return alert
            else:
                logger.error(f"Failed to create alert: {alert_serializer.errors}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}", exc_info=True)
            return None
    
    def _save_inference(self, camera, result, alert_id=None):
        """Same as AnalyzeFrameView"""
        try:
            alert = None
            if alert_id:
                try:
                    alert = Alert.objects.get(pk=alert_id)
                except Alert.DoesNotExist:
                    pass
            
            inference = AIInference.objects.create(
                camera_id=camera,
                detections=result['detections'],
                poses=result['poses'],
                tracks=result['tracks'],
                classification=result['classification'],
                confidence=result['confidence'],
                frame_metadata=result['frame_metadata'],
                processing_time_ms=result['processing_time_ms'],
                alert=alert,
            )
            
            return inference
            
        except Exception as e:
            logger.error(f"Error saving inference: {str(e)}", exc_info=True)
            return None


class FullPipelineView(views.APIView):
    """
    POST /api/ai/full-pipeline/
    
    Run full pipeline analysis (convenience endpoint that combines both options)
    Can accept either frame data or camera_id
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if frame or camera_id provided
        has_frame = 'frame' in request.data
        has_camera_id = 'camera_id' in request.data
        
        if not has_frame and not has_camera_id:
            return Response(
                {'error': 'Either "frame" or "camera_id" must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Route to appropriate view
        if has_frame:
            view = AnalyzeFrameView()
            view.request = request
            view.format_kwarg = None
            return view.post(request)
        else:
            view = ProcessCameraView()
            view.request = request
            view.format_kwarg = None
            return view.post(request)


class ModelInfoView(views.APIView):
    """
    GET /api/ai/model-info/
    
    Get information about loaded AI models
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        model_info = ai_service.get_model_info()
        serializer = ModelInfoSerializer(data=model_info)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(model_info, status=status.HTTP_200_OK)


class InferenceHistoryView(views.APIView):
    """
    GET /api/ai/inference-history/
    
    Get inference history with optional filters
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = AIInference.objects.select_related('camera_id', 'alert').all()
        
        # Apply filters
        camera_id = request.query_params.get('camera_id')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        classification = request.query_params.get('classification')
        if classification:
            queryset = queryset.filter(classification=classification)
        
        min_confidence = request.query_params.get('min_confidence')
        if min_confidence:
            try:
                queryset = queryset.filter(confidence__gte=float(min_confidence))
            except ValueError:
                pass
        
        # Limit results
        limit = request.query_params.get('limit', 50)
        try:
            limit = min(int(limit), 500)
        except ValueError:
            limit = 50
        
        queryset = queryset[:limit]
        
        serializer = AIInferenceSerializer(queryset, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class HealthCheckView(views.APIView):
    """
    GET /api/ai/health/
    
    Check AI service health
    """
    permission_classes = []  # Public endpoint
    
    def get(self, request):
        return Response({
            'status': 'healthy' if ai_service.is_ready() else 'initializing',
            'models_loaded': ai_service.is_ready(),
            'device': ai_service.device,
        }, status=status.HTTP_200_OK)


class StartContinuousMonitorView(views.APIView):
    """
    POST /api/ai/monitor/start/
    
    Start continuous monitoring on a camera (processes live feed at full FPS)
    
    Body:
    {
        "camera_id": "abc123"
    }
    
    Response:
    {
        "success": true,
        "message": "Started continuous monitoring",
        "camera_id": "abc123",
        "camera_name": "Ali Mobile"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from ..services.continuous_monitor import monitor_manager
        
        camera_id = request.data.get('camera_id')
        restart = request.data.get('restart', False)  # Allow restart option
        
        if not camera_id:
            return Response(
                {'error': 'camera_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get camera
        try:
            camera = Camera.objects.get(pk=camera_id)
        except Camera.DoesNotExist:
            return Response(
                {'error': f'Camera not found: {camera_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if AI is ready
        if not ai_service.is_ready():
            return Response(
                {'error': 'AI service not ready. Models still loading.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Check if already running
        existing_stats = monitor_manager.get_monitor_stats(str(camera.id))
        if existing_stats and existing_stats['is_running']:
            if restart:
                # Stop and restart
                logger.info(f"Restarting monitor for camera {camera.id}")
                monitor_manager.stop_monitor(str(camera.id))
                time.sleep(1)  # Give it time to clean up
            else:
                # Already running, return success with current stats
                return Response({
                    'success': True,
                    'message': 'Monitor already running',
                    'already_running': True,
                    'camera_id': str(camera.id),
                    'camera_name': camera.name,
                    'stats': existing_stats,
                }, status=status.HTTP_200_OK)
        
        # Start monitoring
        success = monitor_manager.start_monitor(str(camera.id), camera.rtsp_url)
        
        if success:
            return Response({
                'success': True,
                'message': 'Started continuous monitoring',
                'already_running': False,
                'camera_id': str(camera.id),
                'camera_name': camera.name,
                'rtsp_url_preview': camera.rtsp_url[:50] + '...' if len(camera.rtsp_url) > 50 else camera.rtsp_url,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to start monitoring',
                'camera_id': str(camera.id),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StopContinuousMonitorView(views.APIView):
    """
    POST /api/ai/monitor/stop/
    
    Stop continuous monitoring on a camera
    
    Body:
    {
        "camera_id": "abc123"
    }
    
    Response:
    {
        "success": true,
        "message": "Stopped monitoring",
        "camera_id": "abc123"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from ..services.continuous_monitor import monitor_manager
        
        camera_id = request.data.get('camera_id')
        if not camera_id:
            return Response(
                {'error': 'camera_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = monitor_manager.stop_monitor(camera_id)
        
        if success:
            return Response({
                'success': True,
                'message': 'Stopped monitoring',
                'camera_id': camera_id,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'No monitor found for this camera',
                'camera_id': camera_id,
            }, status=status.HTTP_404_NOT_FOUND)


class MonitorStatusView(views.APIView):
    """
    GET /api/ai/monitor/status/
    
    Get status of all continuous monitors or a specific one
    
    Query params:
    - camera_id (optional): Get status for specific camera
    
    Response:
    {
        "monitors": {
            "abc123": {
                "camera_id": "abc123",
                "is_running": true,
                "frames_processed": 1523,
                "fps": 28.5,
                "elapsed_seconds": 53.4,
                "error_count": 0,
                "last_result": {...}
            }
        },
        "total_monitors": 1
    }
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from ..services.continuous_monitor import monitor_manager
        
        camera_id = request.query_params.get('camera_id')
        
        if camera_id:
            # Get specific monitor status
            stats = monitor_manager.get_monitor_stats(camera_id)
            if stats:
                return Response({
                    'camera_id': camera_id,
                    'monitor': stats
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'camera_id': camera_id,
                    'monitor': None,
                    'message': 'No monitor running for this camera'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get all monitors
            all_stats = monitor_manager.get_all_stats()
            return Response({
                'monitors': all_stats,
                'total_monitors': len(all_stats)
            }, status=status.HTTP_200_OK)

