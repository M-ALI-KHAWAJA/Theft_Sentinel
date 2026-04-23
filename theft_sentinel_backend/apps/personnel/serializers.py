"""
Personnel Serializers
"""
from rest_framework import serializers
from .models import Personnel
from apps.accounts.serializers import UserSerializer


class PersonnelSerializer(serializers.ModelSerializer):
    """Personnel serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = Personnel
        fields = ['id', 'user', 'user_details', 'phone', 'assigned_zones', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_assigned_zones(self, value):
        """Ensure assigned_zones is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Assigned zones must be a list")
        return value


class PersonnelCreateSerializer(serializers.ModelSerializer):
    """Personnel creation serializer"""
    
    class Meta:
        model = Personnel
        fields = ['user', 'phone', 'assigned_zones']
    
    def validate_user(self, value):
        """Check if user already has personnel profile"""
        if Personnel.objects.filter(user=value).exists():
            raise serializers.ValidationError("This user already has a personnel profile")
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if getattr(value, 'tenant_id', None) != getattr(request.user, 'tenant_id', None):
                raise serializers.ValidationError('User must belong to your branch.')
        return value

