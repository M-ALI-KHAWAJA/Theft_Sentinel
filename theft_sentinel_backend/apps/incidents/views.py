"""
Incident Views

RBAC Rules (Incidents are part of alert management):
-----------------------------------------------------
- Admin: Full access to incidents (view, create, update, delete, assign)
- Security In-Charge: Can view, create, update, and assign incidents
- Security Guard: Can view incidents assigned to them only
"""
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .models import Incident
from .serializers import (
    IncidentSerializer,
    IncidentCreateSerializer,
    IncidentStatusUpdateSerializer,
    IncidentAssignSerializer
)
from apps.accounts.permissions import IsAdminOrIncharge, IsApprovedBranchUser
from config.tenant_scope import scoped_incidents

User = get_user_model()


def _incident_queryset_for_user(user):
    qs = scoped_incidents(user).select_related('alert_id', 'assigned_to', 'assigned_by')
    if user.role == 'SECURITY_GUARD':
        qs = qs.filter(assigned_to=user)
    return qs


class IncidentListCreateView(generics.ListCreateAPIView):
    """
    List all incidents or create new
    
    Permissions:
    - Admin & Security In-Charge: Can view all incidents and create new
    - Security Guard: Can only view incidents assigned to them
    """
    queryset = Incident.objects.all()
    permission_classes = [IsAuthenticated, IsApprovedBranchUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IncidentCreateSerializer
        return IncidentSerializer
    
    def get_queryset(self):
        queryset = _incident_queryset_for_user(self.request.user)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        assigned_to = self.request.query_params.get('assigned_to', None)
        if assigned_to and self.request.user.role in ['ADMIN', 'SECURITY_INCHARGE']:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        my_incidents = self.request.query_params.get('my_incidents', None)
        if my_incidents == 'true':
            queryset = queryset.filter(assigned_to=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        if request.user.role == 'SECURITY_GUARD':
            return Response(
                {'error': 'You do not have permission to create incidents.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        alert = serializer.validated_data['alert_id']
        serializer.save(tenant_id=alert.tenant_id)


class IncidentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete incident
    
    Permissions:
    - Admin: Full access (view, update, delete)
    - Security In-Charge: View and update only
    - Security Guard: View only (their assigned incidents)
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser]
    
    def get_queryset(self):
        return _incident_queryset_for_user(self.request.user)
    
    def update(self, request, *args, **kwargs):
        if request.user.role == 'SECURITY_GUARD':
            return Response(
                {'error': 'You do not have permission to update incidents.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        if request.user.role == 'SECURITY_GUARD':
            return Response(
                {'error': 'You do not have permission to update incidents.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if request.user.role not in ['ADMIN', 'SECURITY_INCHARGE']:
            return Response(
                {'error': 'You do not have permission to delete incidents. Only Admin and Security In-Charge can delete incidents.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        if instance.status != 'RESOLVED':
            return Response(
                {'error': 'Only resolved incidents can be deleted. Please resolve the incident first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class IncidentStatusUpdateView(views.APIView):
    """
    Update incident status
    
    Permissions:
    - Admin & Security In-Charge: Can update incident status
    - Security Guard: Can update status of incidents assigned to them
    """
    permission_classes = [IsAuthenticated, IsApprovedBranchUser]
    
    def patch(self, request, pk):
        incident = _incident_queryset_for_user(request.user).filter(pk=pk).first()
        if not incident:
            return Response(
                {'error': 'Incident not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.user.role == 'SECURITY_GUARD':
            if incident.assigned_to != request.user:
                return Response(
                    {'error': 'You can only update incidents assigned to you.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = IncidentStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            incident.status = serializer.validated_data['status']
            if 'notes' in serializer.validated_data:
                incident.notes = serializer.validated_data['notes']
            incident.save()
            return Response(IncidentSerializer(incident).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncidentAssignView(views.APIView):
    """
    Assign incident to a user
    
    Permissions:
    - Admin & Security In-Charge: Can assign incidents
    - Security Guard: Cannot assign incidents
    """
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdminOrIncharge]
    
    def patch(self, request, pk):
        incident = scoped_incidents(request.user).filter(pk=pk).first()
        if not incident:
            return Response(
                {'error': 'Incident not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = IncidentAssignSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(
                    pk=serializer.validated_data['assigned_to'],
                    tenant_id=request.user.tenant_id,
                )
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            incident.assigned_to = user
            incident.assigned_by = request.user
            incident.status = 'ASSIGNED'
            if 'notes' in serializer.validated_data:
                incident.notes = serializer.validated_data['notes']
            incident.save()
            
            return Response(IncidentSerializer(incident).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyIncidentsView(generics.ListAPIView):
    """
    Get incidents assigned to current user
    
    Permissions:
    - All authenticated users can view their assigned incidents
    """
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser]
    
    def get_queryset(self):
        return scoped_incidents(self.request.user).select_related(
            'alert_id', 'assigned_to', 'assigned_by'
        ).filter(
            assigned_to=self.request.user
        ).order_by('-created_at')


class UnassignedIncidentsView(generics.ListAPIView):
    """
    Get unassigned incidents
    
    Permissions:
    - Admin & Security In-Charge: Can view unassigned incidents
    - Security Guard: Cannot view unassigned incidents
    """
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdminOrIncharge]
    
    def get_queryset(self):
        return scoped_incidents(self.request.user).select_related('alert_id', 'assigned_by').filter(
            assigned_to__isnull=True
        ).order_by('-created_at')
