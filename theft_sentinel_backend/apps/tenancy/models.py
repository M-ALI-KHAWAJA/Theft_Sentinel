"""
Multi-tenant models (single DB) for enterprise deployment.

Tenants and Branches are logically isolated via FK scoping — no separate DBs.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_mongodb_backend.fields import ObjectIdAutoField


class Tenant(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    company_name = models.CharField(max_length=255, db_index=True)
    company_address = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.company_name


class Branch(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_SUSPENDED = "SUSPENDED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_SUSPENDED, "Suspended"),
    ]

    id = ObjectIdAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="branches")

    branch_name = models.CharField(max_length=255, db_index=True)
    admin_name = models.CharField(max_length=255)
    admin_cnic = models.CharField(max_length=30, db_index=True)
    admin_email = models.EmailField(max_length=255, db_index=True)
    admin_phone = models.CharField(max_length=30, blank=True, default="")

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "branches"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "branch_name"], name="branches_tenant__c5ffaa_idx"),
            models.Index(fields=["status", "-created_at"], name="branches_status_bf7330_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.tenant.company_name} — {self.branch_name}"

    def save(self, *args, **kwargs):
        if self.admin_cnic:
            from apps.accounts.cnic import validate_cnic_available

            exclude = {
                "branches": [self.pk] if self.pk else [],
                "branch_admin_user_branch_ids": [self.pk] if self.pk else [],
            }
            self.admin_cnic = validate_cnic_available(self.admin_cnic, exclude=exclude)
        super().save(*args, **kwargs)


class SuperAdminProfile(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="super_admin_profile"
    )

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=30, blank=True, default="")

    partners_count = models.PositiveSmallIntegerField(default=0)
    partners = models.JSONField(default=list)  # [{name, cnic}]

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "super_admin_profile"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"SuperAdminProfile({self.user.email})"

    def save(self, *args, **kwargs):
        if self.partners:
            from apps.accounts.cnic import (
                ensure_unique_in_payload,
                normalize_cnic_value,
                validate_cnic_available,
            )

            cnics = [partner.get("cnic") for partner in self.partners or []]
            ensure_unique_in_payload(cnics)
            normalized_partners = []
            for partner in self.partners:
                item = dict(partner)
                item["cnic"] = normalize_cnic_value(item.get("cnic"))
                validate_cnic_available(
                    item["cnic"],
                    exclude={"super_admin_profiles": [self.pk] if self.pk else []},
                )
                normalized_partners.append(item)
            self.partners = normalized_partners
        super().save(*args, **kwargs)


class BranchPasswordResetRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_password_reset_requests",
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="password_reset_requests")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_password_reset_requests",
    )

    class Meta:
        db_table = "branch_password_reset_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="branch_pass_status_ad0e90_idx"),
            models.Index(fields=["branch", "-created_at"], name="branch_pass_branch__81e9a8_idx"),
        ]

    def __str__(self) -> str:
        return f"ResetRequest({self.user.email}, {self.status})"

