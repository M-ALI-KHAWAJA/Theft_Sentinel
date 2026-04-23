"""
Tracking Record Serializers
"""
from rest_framework import serializers
from .models import TrackingRecord
from apps.cameras.serializers import CameraSerializer


class TrackingRecordSerializer(serializers.ModelSerializer):
    """Tracking Record serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    camera_details = CameraSerializer(source='camera_id', read_only=True)
    
    class Meta:
        model = TrackingRecord
        fields = ['id', 'person_id', 'camera_id', 'camera_details', 'vector', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class TrackingRecordCreateSerializer(serializers.ModelSerializer):
    """Tracking Record creation serializer"""
    
    class Meta:
        model = TrackingRecord
        fields = ['person_id', 'camera_id', 'vector']
    
    def validate_vector(self, value):
        """Ensure vector is a dict or list"""
        if not isinstance(value, (dict, list)):
            raise serializers.ValidationError("Vector must be a dictionary or list")
        return value

    def validate_camera_id(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if getattr(value, 'tenant_id', None) != getattr(request.user, 'tenant_id', None):
                raise serializers.ValidationError('Camera must belong to your branch.')
        return value

