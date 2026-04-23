"""
Serializers for User and Authentication
"""
import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

from .models import PasswordResetRequest, SuperAdminProfile

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
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    tenant_status = serializers.SerializerMethodField()
    tenant_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'tenant_id',
            'tenant_name',
            'tenant_status',
            'tenant_display',
            'is_active',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'tenant_id',
            'tenant_name',
            'tenant_status',
            'tenant_display',
        ]

    def get_tenant_id(self, obj):
        return str(obj.tenant_id) if getattr(obj, 'tenant_id', None) else None

    def get_tenant_name(self, obj):
        t = getattr(obj, 'tenant', None)
        return t.name if t else None

    def get_tenant_status(self, obj):
        t = getattr(obj, 'tenant', None)
        return t.status if t else None

    def get_tenant_display(self, obj):
        """Branch label: ``{tenant.name} - {company}`` when ``company_name`` exists on Tenant."""
        t = getattr(obj, 'tenant', None)
        if not t:
            return None
        company = (getattr(t, 'company_name', None) or '').strip()
        if company:
            return f'{t.name} - {company}'
        return t.name

    def validate_role(self, value):
        """At most one active Admin per branch tenant."""
        if value != 'ADMIN':
            return value
        request = self.context.get('request')
        tenant = getattr(request.user, 'tenant', None) if request and request.user.is_authenticated else None
        if tenant is None and self.instance and getattr(self.instance, 'tenant', None):
            tenant = self.instance.tenant
        qs = User.objects.filter(role='ADMIN', is_active=True, tenant=tenant)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Only one Admin can exist per branch. An Admin user already exists for this tenant.'
            )
        return value

    def validate_username(self, value):
        v = (value or '').strip()
        if not v:
            raise serializers.ValidationError('This field may not be blank.')
        inst = self.instance
        tenant = getattr(inst, 'tenant', None) if inst else None
        if tenant is None:
            return v
        qs = User.objects.filter(username=v, tenant=tenant)
        if inst:
            qs = qs.exclude(pk=inst.pk)
        if qs.exists():
            raise serializers.ValidationError('Username already exists in this branch')
        return v

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if not email:
            raise serializers.ValidationError('This field may not be blank.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Email already exists')
        return email


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer (Admin only)"""
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[c for c in User.ROLE_CHOICES if c[0] != 'SUPER_ADMIN']
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'is_active']
    
    def validate_role(self, value):
        if value == 'SUPER_ADMIN':
            raise serializers.ValidationError('Invalid role.')
        request = self.context.get('request')
        tenant = getattr(request.user, 'tenant', None) if request and request.user.is_authenticated else None
        if value == 'ADMIN' and User.objects.filter(role='ADMIN', is_active=True, tenant=tenant).exists():
            raise serializers.ValidationError(
                'Only one Admin can exist per branch. An Admin user already exists for this tenant.'
            )
        return value

    def validate_username(self, value):
        v = (value or '').strip()
        if not v:
            raise serializers.ValidationError('This field may not be blank.')
        request = self.context.get('request')
        tenant = getattr(request.user, 'tenant', None) if request and request.user.is_authenticated else None
        if tenant and User.objects.filter(username=v, tenant=tenant).exists():
            raise serializers.ValidationError('Username already exists in this branch')
        return v

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Email already exists')
        return email

    def validate_password(self, value):
        validate_password_strength(value)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        request = self.context.get('request')
        tenant = getattr(request.user, 'tenant', None) if request and request.user.is_authenticated else None
        email = validated_data.pop('email')
        return User.objects.create_user(email, password, tenant=tenant, **validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer with user data"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # USERNAME_FIELD is ``email``; clients still POST ``username`` (legacy).
        self.fields[self.username_field].required = False
        self.fields['username'] = serializers.CharField(
            write_only=True, required=False, allow_blank=True, default=''
        )

    def validate(self, attrs):
        uid_field = self.username_field
        raw = (attrs.get(uid_field) or attrs.pop('username', None) or '').strip()
        if not raw:
            raise serializers.ValidationError(
                {uid_field: 'Enter your email address (or username if it is unique on the platform).'}
            )
        if '@' in raw:
            attrs[uid_field] = User.objects.normalize_email(raw)
        else:
            uname_qs = User.objects.filter(username__iexact=raw)
            if uname_qs.count() > 1:
                raise serializers.ValidationError(
                    {
                        'detail': (
                            'This username exists on more than one branch. '
                            'Sign in with your email address.'
                        )
                    }
                )
            if uname_qs.count() == 1:
                attrs[uid_field] = uname_qs.first().email
            else:
                attrs[uid_field] = raw

        attrs.pop('username', None)
        data = super().validate(attrs)
        user = self.user
        if user.role != 'SUPER_ADMIN':
            if not getattr(user, 'tenant_id', None):
                raise serializers.ValidationError(
                    {'detail': 'No branch is assigned to this account.'}
                )
            tenant = getattr(user, 'tenant', None)
            if tenant is None or tenant.status != 'APPROVED':
                raise serializers.ValidationError(
                    {'detail': 'Your branch registration is not approved yet.'}
                )

        tenant = getattr(user, 'tenant', None)
        company = (getattr(tenant, 'company_name', None) or '').strip() if tenant else ''
        tenant_display = None
        if tenant:
            tenant_display = f'{tenant.name} - {company}' if company else tenant.name

        data['user'] = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'tenant_id': str(user.tenant_id) if user.tenant_id else None,
            'tenant_name': tenant.name if tenant else None,
            'tenant_status': tenant.status if tenant else None,
            'tenant_display': tenant_display,
        }

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        if user.tenant_id:
            token['tenant_id'] = str(user.tenant_id)
        return token


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
        if user.role not in ('ADMIN', 'SUPER_ADMIN'):
            raise serializers.ValidationError(NON_ADMIN_FORGOT_PASSWORD_MESSAGE)
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password serializer"""

    # Path/query tokens can be long; must not use implicit short max_length.
    token = serializers.CharField(required=True, max_length=256, trim_whitespace=True)
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


class PasswordResetRequestCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reason = serializers.CharField(required=True, allow_blank=False)

    def validate_reason(self, value):
        s = (value or '').strip()
        if len(s) < 10:
            raise serializers.ValidationError(
                'Please provide a clear reason (at least 10 characters).'
            )
        return s

    def validate_email(self, value):
        """Branch Admin (tenant ``ADMIN``) only — queue for Super Admin approval."""
        user = User.objects.filter(email__iexact=value.strip().lower()).first()
        if not user or user.role != 'ADMIN' or not user.is_active:
            raise serializers.ValidationError('Invalid Branch Admin email')
        self.context['resolved_user'] = user
        return user.email


class PartnerEntrySerializer(serializers.Serializer):
    partner_name = serializers.CharField(max_length=255)
    partner_cnic = serializers.CharField(max_length=20)

    def validate_partner_cnic(self, value):
        s = (value or '').strip()
        if not re.match(r'^\d{5}-\d{7}-\d{1}$', s):
            raise serializers.ValidationError('CNIC must be in format 12345-1234567-1.')
        return s


class CreateSuperAdminSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, min_length=8)
    partners = PartnerEntrySerializer(many=True, required=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value.strip().lower()).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value.strip().lower()

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def validate_partners(self, value):
        if not value:
            raise serializers.ValidationError('At least one partner is required.')
        if len(value) > 3:
            raise serializers.ValidationError('A maximum of 3 partners is allowed.')
        return value


class PasswordResetRequestReadSerializer(serializers.ModelSerializer):
    """MongoDB ObjectId PKs must not use DRF's default integer ``id`` field."""

    id = serializers.CharField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.SerializerMethodField()

    class Meta:
        model = PasswordResetRequest
        fields = ['id', 'user_id', 'user_email', 'reason', 'status', 'created_at']
        read_only_fields = [
            'id',
            'user_id',
            'user_email',
            'reason',
            'status',
            'created_at',
        ]

    def get_user_id(self, obj):
        return str(obj.user_id) if obj.user_id else None


class SuperAdminProfileSerializer(serializers.ModelSerializer):
    """Read/update Super Admin profile (partners validated like bootstrap)."""

    name = serializers.CharField(source='display_name', max_length=255)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = SuperAdminProfile
        fields = ['name', 'email', 'phone', 'partners']
        read_only_fields = ['email']

    def validate_partners(self, value):
        if value is None:
            return value
        if not isinstance(value, list):
            raise serializers.ValidationError('Partners must be a list.')
        if len(value) > 3:
            raise serializers.ValidationError('A maximum of 3 partners is allowed.')
        if not value:
            return []
        cleaned = []
        for item in value:
            pe = PartnerEntrySerializer(data=item)
            pe.is_valid(raise_exception=True)
            cleaned.append(pe.validated_data)
        return cleaned
