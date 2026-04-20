"""
Surveillance Event Serializers
"""
from rest_framework import serializers
from .models import SurveillanceEvent
from apps.cameras.serializers import CameraSerializer


class SurveillanceEventSerializer(serializers.ModelSerializer):
    """Surveillance Event serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    camera_details = CameraSerializer(source='camera_id', read_only=True)
    
    class Meta:
        model = SurveillanceEvent
        fields = ['id', 'camera_id', 'camera_details', 'event_type', 'frame_url', 'ai_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class SurveillanceEventCreateSerializer(serializers.ModelSerializer):
    """Surveillance Event creation serializer"""
    
    class Meta:
        model = SurveillanceEvent
        fields = ['camera_id', 'event_type', 'frame_url', 'ai_data']
    
    def validate_ai_data(self, value):
        """Ensure ai_data is a dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("AI data must be a dictionary")
        return value

