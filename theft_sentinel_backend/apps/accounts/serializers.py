"""
Serializers for User and Authentication
"""
import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

NON_ADMIN_FORGOT_PASSWORD_MESSAGE = (
    "Only admin can change password from here. Contact admin if you have lost your password."
)

PASSWORD_COMPLEXITY_ERROR = (
    "Password must be at least 8 characters long and include at least one uppercase "
    "letter (A–Z), one lowercase letter (a–z), one number (0–9), and one special "
    "character (e.g. @, #, $, %)."
)


def validate_password_strength(value):
    """
    Enforce password rules for set, change, and reset flows.
    Raises ValidationError with a single user-facing message if invalid.
    """
    if not value or len(value) < 8:
        raise serializers.ValidationError(PASSWORD_COMPLEXITY_ERROR)
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError(PASSWORD_COMPLEXITY_ERROR)
    if not re.search(r"[a-z]", value):
        raise serializers.ValidationError(PASSWORD_COMPLEXITY_ERROR)
    if not re.search(r"[0-9]", value):
        raise serializers.ValidationError(PASSWORD_COMPLEXITY_ERROR)
    if not re.search(r"[^A-Za-z0-9]", value):
        raise serializers.ValidationError(PASSWORD_COMPLEXITY_ERROR)
    return value


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    id = serializers.CharField(read_only=True)  # MongoDB ObjectId as string
    role = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer (Admin only)"""
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'is_active']
    
    def validate_role(self, value):
        """Ensure only one Admin can exist"""
        if value == 'ADMIN':
            if User.objects.filter(role='ADMIN', is_active=True).exists():
                raise serializers.ValidationError(
                    "Only one Admin can exist in the system. An Admin user already exists."
                )
        return value

    def validate_password(self, value):
        validate_password_strength(value)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with user data"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': str(self.user.id),
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
        }
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    
    def validate_new_password(self, value):
        validate_password_strength(value)
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    """Forgot password serializer - Admin only"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that email exists and belongs to an admin"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(NON_ADMIN_FORGOT_PASSWORD_MESSAGE)
        if user.role != 'ADMIN':
            raise serializers.ValidationError(NON_ADMIN_FORGOT_PASSWORD_MESSAGE)
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password serializer"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return attrs
    
    def validate_new_password(self, value):
        validate_password_strength(value)
        return value
