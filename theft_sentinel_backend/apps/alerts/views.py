"""
Alert Views

RBAC Rules:
-----------
- Admin: View all alerts & alert history, Delete alerts
- Security In-Charge: View all alerts & alert history, Cannot delete alerts
- Security Guard: View real-time alerts only (no history), Cannot delete alerts
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import Alert
from .serializers import AlertSerializer, AlertCreateSerializer, AlertAcknowledgeSerializer
from apps.accounts.permissions import IsAdminOrIncharge, CanViewAlerts, CanDeleteAlerts, IsApprovedBranchUser
from config.tenant_scope import scoped_alerts


class AlertListCreateView(generics.ListCreateAPIView):
    """
    List all alerts or create new
    
    Permissions:
    - Admin & Security In-Charge: Can view all alerts including history
    - Security Guard: Can view alerts (filtered in queryset)
    - All: Can create alerts (from AI system)
    """
    queryset = Alert.objects.all()
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanViewAlerts]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertCreateSerializer
        return AlertSerializer
    
    def get_queryset(self):
        queryset = scoped_alerts(self.request.user).select_related('camera_id')
        
        if self.request.user.role == 'SECURITY_GUARD':
            time_threshold = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(timestamp__gte=time_threshold)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        acknowledged_param = self.request.query_params.get('acknowledged', None)
        if acknowledged_param is not None:
            if acknowledged_param.lower() == 'true':
                queryset = queryset.filter(status__in=['ACKED', 'RESOLVED'])
            elif acknowledged_param.lower() == 'false':
                queryset = queryset.filter(status='ACTIVE')
        
        camera_id = self.request.query_params.get('camera_id', None)
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        alert_type = self.request.query_params.get('alert_type', None)
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        if self.request.user.role in ['ADMIN', 'SECURITY_INCHARGE']:
            start_date = self.request.query_params.get('start_date', None)
            if start_date:
                queryset = queryset.filter(timestamp__gte=start_date)
            
            end_date = self.request.query_params.get('end_date', None)
            if end_date:
                queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete alert
    
    Permissions:
    - Admin: Full access (view, update, delete)
    - Security In-Charge: View and update only
    - Security Guard: View only (recent alerts)
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanViewAlerts]
    
    def get_queryset(self):
        queryset = scoped_alerts(self.request.user).select_related('camera_id')
        
        if self.request.user.role == 'SECURITY_GUARD':
            time_threshold = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(timestamp__gte=time_threshold)
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'You do not have permission to delete alerts. Only Admin can delete alerts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if request.user.role == 'SECURITY_GUARD':
            return Response(
                {'error': 'You do not have permission to update alerts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        if request.user.role == 'SECURITY_GUARD':
            return Response(
                {'error': 'You do not have permission to update alerts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)


class AlertAcknowledgeView(views.APIView):
    """
    Acknowledge or resolve an alert
    
    Permissions:
    - Admin & Security In-Charge: Can acknowledge/resolve alerts
    - Security Guard: Cannot acknowledge/resolve alerts
    
    When guard_id is provided, creates an incident with status ASSIGNED
    """
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdminOrIncharge]
    
    def patch(self, request, pk):
        from django.contrib.auth import get_user_model
        from apps.incidents.models import Incident
        
        User = get_user_model()
        
        alert = scoped_alerts(request.user).filter(pk=pk).first()
        if not alert:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AlertAcknowledgeSerializer(data=request.data)
        if serializer.is_valid():
            alert.status = serializer.validated_data['status']
            alert.save()
            
            guard_email = serializer.validated_data['guard_email']
            comment = serializer.validated_data.get('comment', '')
            
            try:
                guard = User.objects.get(
                    email=guard_email,
                    role='SECURITY_GUARD',
                    tenant_id=request.user.tenant_id,
                )
                Incident.objects.create(
                    alert_id=alert,
                    tenant_id=alert.tenant_id,
                    assigned_to=guard,
                    assigned_by=request.user,
                    status='ASSIGNED',
                    notes=comment
                )
            except User.DoesNotExist:
                return Response(
                    {'error': 'Guard not found or invalid guard email'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {'error': f'Failed to create incident: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(AlertSerializer(alert).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActiveAlertsView(generics.ListAPIView):
    """
    Get all active alerts
    
    Permissions:
    - All authenticated users can view active alerts
    - Security Guard: Only recent active alerts (last 24 hours)
    """
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanViewAlerts]
    
    def get_queryset(self):
        queryset = scoped_alerts(self.request.user).select_related('camera_id').filter(
            status='ACTIVE'
        )
        
        if self.request.user.role == 'SECURITY_GUARD':
            time_threshold = timezone.now() - timedelta(hours=24)
            queryset = queryset.filter(timestamp__gte=time_threshold)
        
        return queryset.order_by('-timestamp')


class RecentAlertsView(generics.ListAPIView):
    """
    Get alerts from the last 24 hours
    
    Permissions:
    - All authenticated users can view recent alerts
    """
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanViewAlerts]
    
    def get_queryset(self):
        time_threshold = timezone.now() - timedelta(hours=24)
        return scoped_alerts(self.request.user).select_related('camera_id').filter(
            timestamp__gte=time_threshold
        ).order_by('-timestamp')


class AlertDeleteView(views.APIView):
    """
    Delete an alert
    
    Permissions:
    - Only Admin can delete alerts
    """
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanDeleteAlerts]
    
    def delete(self, request, pk):
        alert = scoped_alerts(request.user).filter(pk=pk).first()
        if not alert:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        alert.delete()
        return Response(
            {'message': 'Alert deleted successfully'},
            status=status.HTTP_200_OK
        )
