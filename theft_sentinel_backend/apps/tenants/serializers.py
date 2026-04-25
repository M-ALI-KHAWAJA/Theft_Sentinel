"""
Serializers for tenant (branch) registration and super-admin APIs.
"""
import re

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Tenant, TenantQuery
from apps.accounts.serializers import validate_password_strength

User = get_user_model()

GMAIL_SUFFIX = '@gmail.com'
CNIC_RE = re.compile(r'^\d{5}-\d{7}-\d{1}$')
# E.164-style: + then digits only (e.g. +923001234567)
PHONE_NUMBER_RE = re.compile(r'^\+\d{8,20}$')


class BranchRegisterSerializer(serializers.Serializer):
    """Public branch registration: creates pending tenant + branch admin user."""

    branch_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    cnic = serializers.CharField(max_length=20)
    phone_number = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        lower = value.lower().strip()
        if not lower.endswith(GMAIL_SUFFIX):
            raise serializers.ValidationError('Email must be a Gmail address (@gmail.com).')
        if User.objects.filter(email__iexact=lower).exists():
            raise serializers.ValidationError('This email is already registered.')
        if Tenant.objects.filter(email__iexact=lower).exists():
            raise serializers.ValidationError('This email is already used for a branch registration.')
        return lower

    def validate_cnic(self, value):
        s = (value or '').strip()
        if not CNIC_RE.match(s):
            raise serializers.ValidationError('CNIC must be in format 12345-1234567-1.')
        return s

    def validate_phone_number(self, value):
        s = (value or '').strip()
        if not s:
            raise serializers.ValidationError('Phone number is required.')
        if not s.startswith('+'):
            raise serializers.ValidationError('Phone number must start with + (international format).')
        if not all(ch.isdigit() for ch in s[1:]):
            raise serializers.ValidationError('Phone number must contain only digits after +.')
        if not PHONE_NUMBER_RE.match(s):
            raise serializers.ValidationError('Enter a valid international phone number (e.g. +923001234567).')
        return s

    def validate_branch_name(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('Branch name is required.')
        return value.strip()

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def create(self, validated_data):
        email = validated_data['email']
        tenant = Tenant.objects.create(
            name=validated_data['branch_name'],
            email=email,
            cnic=validated_data['cnic'],
            phone=validated_data['phone_number'],
            status='PENDING',
        )
        base_username = email.split('@')[0].replace('.', '_')[:120]
        username = base_username
        n = 0
        while User.objects.filter(username=username, tenant=tenant).exists():
            n += 1
            username = f'{base_username}_{n}'[:150]
        user = User.objects.create_user(
            email,
            validated_data['password'],
            username=username,
            role='ADMIN',
            tenant=tenant,
            is_active=True,
        )
        return tenant, user


class TenantListSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'email', 'cnic', 'phone', 'status', 'created_at']
        read_only_fields = fields


class BranchTenantProfileSerializer(serializers.ModelSerializer):
    """Branch Admin: read branch context; update CNIC and phone only."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'email', 'cnic', 'phone', 'status']

    def validate_cnic(self, value):
        s = (value or '').strip()
        if not CNIC_RE.match(s):
            raise serializers.ValidationError('CNIC must be in format 12345-1234567-1.')
        return s

    def validate_phone(self, value):
        s = (value or '').strip()
        if not s:
            return s
        if not s.startswith('+'):
            raise serializers.ValidationError('Phone number must start with + (international format).')
        if not all(ch.isdigit() for ch in s[1:]):
            raise serializers.ValidationError('Phone number must contain only digits after +.')
        if not PHONE_NUMBER_RE.match(s):
            raise serializers.ValidationError('Enter a valid international phone number (e.g. +923001234567).')
        return s


class TenantStatusSerializer(serializers.Serializer):
    """Optional note for reject — kept minimal."""

    note = serializers.CharField(required=False, allow_blank=True, default='')


class TenantQueryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantQuery
        fields = ['message']

    def validate_message(self, value):
        s = (value or '').strip()
        if len(s) < 5:
            raise serializers.ValidationError('Please describe your issue (at least 5 characters).')
        return s


class TenantQuerySerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = TenantQuery
        fields = ['id', 'message', 'response', 'status', 'created_at', 'created_by_username']
        read_only_fields = ['id', 'message', 'response', 'status', 'created_at', 'created_by_username']

    def get_created_by_username(self, obj):
        u = getattr(obj, 'created_by', None)
        return u.username if u else None


class TenantQueryAdminSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)  # Mongo ObjectId
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_email = serializers.EmailField(source='tenant.email', read_only=True)
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = TenantQuery
        fields = [
            'id',
            'tenant_name',
            'tenant_email',
            'created_by_username',
            'message',
            'response',
            'status',
            'created_at',
        ]
        read_only_fields = fields

    def get_created_by_username(self, obj):
        u = getattr(obj, 'created_by', None)
        return u.username if u else None


class TenantQueryAnswerSerializer(serializers.Serializer):
    response = serializers.CharField(required=True, allow_blank=False)

    def validate_response(self, value):
        s = (value or '').strip()
        if len(s) < 1:
            raise serializers.ValidationError('Response is required.')
        return s
