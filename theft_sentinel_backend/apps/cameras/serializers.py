"""
Camera Serializers
"""
from rest_framework import serializers
from .models import Camera


class CameraSerializer(serializers.ModelSerializer):
    """Camera serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    
    class Meta:
        model = Camera
        fields = [
            'id', 'name', 'rtsp_url', 'location', 'zone',
            'status', 'created_at', 'ai_monitoring_enabled',
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_status(self, value):
        """Validate status"""
        if value not in ['ONLINE', 'OFFLINE']:
            raise serializers.ValidationError("Status must be ONLINE or OFFLINE")
        return value


class CameraCreateSerializer(serializers.ModelSerializer):
    """Camera creation serializer"""
    
    class Meta:
        model = Camera
        fields = ['name', 'rtsp_url', 'location', 'zone', 'status']


class CameraStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating camera status"""
    status = serializers.ChoiceField(choices=['ONLINE', 'OFFLINE'])

