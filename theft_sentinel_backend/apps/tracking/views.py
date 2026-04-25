"""
Tracking Views
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import TrackingRecord
from .serializers import TrackingRecordSerializer, TrackingRecordCreateSerializer
from .services import TrackingService
from rest_framework.exceptions import NotFound


class TrackingRecordListCreateView(generics.ListCreateAPIView):
    """List all tracking records or create new"""
    queryset = TrackingRecord.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TrackingRecordCreateSerializer
        return TrackingRecordSerializer
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except NotFound:
            # Handle out-of-bounds pagination gracefully
            return Response({
                'count': self.get_queryset().count(),
                'next': None,
                'previous': None,
                'results': []
            })
    
    def get_queryset(self):
        queryset = TrackingRecord.objects.select_related('camera_id').all()
        
        # Filter by person_id
        person_id = self.request.query_params.get('person_id', None)
        if person_id:
            queryset = queryset.filter(person_id=person_id)
        
        # Filter by camera
        camera_id = self.request.query_params.get('camera_id', None)
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


class TrackingRecordDetailView(generics.RetrieveAPIView):
    """Retrieve a tracking record"""
    queryset = TrackingRecord.objects.all()
    serializer_class = TrackingRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TrackingRecord.objects.select_related('camera_id').all()


class PersonTrackingPathView(views.APIView):
    """Get tracking path for a person across cameras"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, person_id):
        """
        Get tracking path for a person
        
        Query params:
        - time_window: Time window in minutes (default: 60)
        """
        time_window = int(request.query_params.get('time_window', 60))
        
        tracking_path = TrackingService.track_person_across_cameras(
            person_id=person_id,
            time_window_minutes=time_window
        )
        
        return Response({
            'person_id': person_id,
            'time_window_minutes': time_window,
            'tracking_path': tracking_path,
            'total_locations': len(tracking_path)
        }, status=status.HTTP_200_OK)


class TrackingIngestView(views.APIView):
    """
    Ingest tracking data from AI detection system
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Receive and process tracking data
        
        Expected payload:
        {
            "camera_id": 1,
            "vector": {...} or [...],
            "person_id": "optional - will be generated if not provided"
        }
        """
        data = request.data.copy()
        
        # Generate person_id if not provided
        if 'person_id' not in data or not data['person_id']:
            vector_data = data.get('vector', {})
            data['person_id'] = TrackingService.generate_person_id(vector_data)
        
        serializer = TrackingRecordCreateSerializer(data=data)
        
        if serializer.is_valid():
            tracking_record = serializer.save()
            
            return Response({
                'tracking_record': TrackingRecordSerializer(tracking_record).data,
                'message': 'Tracking data ingested successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TrackingStatsView(views.APIView):
    """Return aggregate tracking statistics for the dashboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = TrackingRecord.objects.count()
        unique_persons = (
            TrackingRecord.objects
            .values_list('person_id', flat=True)
            .distinct()
            .count() if total else 0
        )

        # Recent activity (last 24 hours)
        since = timezone.now() - timedelta(hours=24)
        recent = TrackingRecord.objects.filter(timestamp__gte=since).count()

        return Response({
            'total_records': total,
            'unique_persons': unique_persons,
            'recent_24h': recent,
        })
