"""
Incident Serializers
"""
from rest_framework import serializers
from .models import Incident
from apps.alerts.serializers import AlertSerializer
from apps.accounts.serializers import UserSerializer


class IncidentSerializer(serializers.ModelSerializer):
    """Incident serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    alert_id = serializers.SerializerMethodField()  # Convert ObjectId to string
    assigned_to = serializers.SerializerMethodField()  # Convert ObjectId to string
    assigned_by = serializers.SerializerMethodField()  # Convert ObjectId to string
    alert_details = AlertSerializer(source='alert_id', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_details = UserSerializer(source='assigned_by', read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'alert_id', 'alert_details', 'assigned_to', 'assigned_to_details',
            'assigned_by', 'assigned_by_details', 'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_alert_id(self, obj):
        """Convert alert ObjectId to string"""
        return str(obj.alert_id.id) if obj.alert_id else None
    
    def get_assigned_to(self, obj):
        """Convert assigned_to ObjectId to string"""
        return str(obj.assigned_to.id) if obj.assigned_to else None
    
    def get_assigned_by(self, obj):
        """Convert assigned_by ObjectId to string"""
        return str(obj.assigned_by.id) if obj.assigned_by else None


class IncidentCreateSerializer(serializers.ModelSerializer):
    """Incident creation serializer"""
    
    class Meta:
        model = Incident
        fields = ['alert_id', 'assigned_to', 'notes']


class IncidentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating incident status"""
    status = serializers.ChoiceField(choices=['CREATED', 'ASSIGNED', 'ACKNOWLEDGED', 'RESOLVED'])
    notes = serializers.CharField(required=False, allow_blank=True)


class IncidentAssignSerializer(serializers.Serializer):
    """Serializer for assigning incident to user"""
    assigned_to = serializers.CharField()  # MongoDB ObjectId as string
    notes = serializers.CharField(required=False, allow_blank=True)

