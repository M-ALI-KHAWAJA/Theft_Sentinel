from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import validate_password_strength
from .models import Tenant, Branch, SuperAdminProfile, BranchPasswordResetRequest

User = get_user_model()


class SuperAdminExistsSerializer(serializers.Serializer):
    exists = serializers.BooleanField()


class SuperAdminCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=30, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, min_length=8)
    partners_count = serializers.IntegerField(min_value=0, max_value=3)
    partner_names = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=True,
        required=False,
        default=list,
    )
    partner_cnics = serializers.ListField(
        child=serializers.CharField(max_length=30),
        allow_empty=True,
        required=False,
        default=list,
    )

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        count = attrs.get("partners_count", 0)
        names = attrs.get("partner_names") or []
        cnics = attrs.get("partner_cnics") or []
        if count != len(names) or count != len(cnics):
            raise serializers.ValidationError(
                {"partners_count": "Partner count must match provided names and CNICs."}
            )
        return attrs


class TenantBranchRegistrationSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    branch_name = serializers.CharField(max_length=255)
    admin_name = serializers.CharField(max_length=255)
    cnic = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=30)
    company_address = serializers.CharField(max_length=512)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class BranchSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    tenant_id = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_address = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = [
            "id",
            "tenant_id",
            "company_name",
            "company_address",
            "branch_name",
            "admin_name",
            "admin_cnic",
            "admin_email",
            "admin_phone",
            "status",
            "created_at",
        ]

    def get_tenant_id(self, obj):
        return str(obj.tenant_id) if hasattr(obj, "tenant_id") else (str(obj.tenant.id) if obj.tenant else None)

    def get_company_name(self, obj):
        return obj.tenant.company_name if obj.tenant else None

    def get_company_address(self, obj):
        return obj.tenant.company_address if obj.tenant else None


class BranchStatusUpdateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "suspend", "reapprove"])


class SuperAdminProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user_id = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = SuperAdminProfile
        fields = [
            "id",
            "user_id",
            "email",
            "full_name",
            "phone_number",
            "partners_count",
            "partners",
            "created_at",
        ]

    def get_user_id(self, obj):
        return str(obj.user.id) if obj.user else None

    def get_email(self, obj):
        return obj.user.email if obj.user else None


class SuperAdminProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    partners_count = serializers.IntegerField(min_value=0, max_value=3, required=False)
    partner_names = serializers.ListField(
        child=serializers.CharField(max_length=255, allow_blank=True), required=False, allow_empty=True
    )
    partner_cnics = serializers.ListField(
        child=serializers.CharField(max_length=30, allow_blank=True), required=False, allow_empty=True
    )

    def validate(self, attrs):
        if "partners_count" in attrs:
            count = attrs["partners_count"]
            names = [name.strip() for name in attrs.get("partner_names") or []]
            cnics = [cnic.strip() for cnic in attrs.get("partner_cnics") or []]
            if names is None or cnics is None:
                raise serializers.ValidationError(
                    "partner_names and partner_cnics are required when updating partners_count."
                )
            if count != len(names) or count != len(cnics):
                raise serializers.ValidationError(
                    {"partners_count": "Partner count must match provided names and CNICs."}
                )
            errors = {}
            blank_names = [f"Partner name #{idx + 1} is required." for idx, name in enumerate(names) if not name]
            blank_cnics = [f"Partner CNIC #{idx + 1} is required." for idx, cnic in enumerate(cnics) if not cnic]
            if blank_names:
                errors["partner_names"] = blank_names
            if blank_cnics:
                errors["partner_cnics"] = blank_cnics
            if errors:
                raise serializers.ValidationError(errors)
            attrs["partner_names"] = names
            attrs["partner_cnics"] = cnics
        return attrs


class BranchAdminProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(source="admin_name")
    email = serializers.EmailField(source="admin_email")
    cnic = serializers.CharField(source="admin_cnic")
    phone_number = serializers.CharField(source="admin_phone", allow_blank=True)
    company_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField()
    address = serializers.SerializerMethodField()
    registration_date = serializers.DateTimeField(source="created_at")

    def get_company_name(self, obj):
        return obj.tenant.company_name if obj.tenant else None

    def get_address(self, obj):
        return obj.tenant.company_address if obj.tenant else ""


class BranchAdminProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    cnic = serializers.CharField(max_length=30)
    phone_number = serializers.CharField(max_length=30, allow_blank=True, required=False)
    company_name = serializers.CharField(max_length=255)
    branch_name = serializers.CharField(max_length=255)
    address = serializers.CharField(max_length=512, allow_blank=True, required=False)

    def validate_email(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        qs = User.objects.filter(email=value)
        if user and getattr(user, "pk", None):
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("Email already exists.")
        return value


class SuperAdminForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class BranchAdminResetRequestCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reason = serializers.CharField()


class BranchPasswordResetRequestSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user_email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    branch_id = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = BranchPasswordResetRequest
        fields = [
            "id",
            "user_email",
            "username",
            "branch_id",
            "branch_name",
            "company_name",
            "reason",
            "status",
            "created_at",
            "reviewed_at",
        ]

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_branch_id(self, obj):
        return str(obj.branch.id) if obj.branch else None

    def get_branch_name(self, obj):
        return obj.branch.branch_name if obj.branch else None

    def get_company_name(self, obj):
        return obj.branch.tenant.company_name if obj.branch and obj.branch.tenant else None

