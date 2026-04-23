"""
Tenant (branch) model for multi-tenancy.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django_mongodb_backend.fields import ObjectIdAutoField


class Tenant(models.Model):
    """One tenant = one branch."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = ObjectIdAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    cnic = models.CharField(max_length=20, db_index=True)
    phone = models.CharField(max_length=32, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def phone_number(self):
        """Branch SMS number (same as ``phone`` field)."""
        return (self.phone or '').strip()


class TenantQuery(models.Model):
    """Branch-submitted message to platform Super Admin."""

    STATUS_CHOICES = [
        ('PENDING_ADMIN_APPROVAL', 'Pending admin approval'),
        ('PENDING_SUPERADMIN', 'Pending super admin'),
        ('ANSWERED', 'Answered'),
    ]

    id = ObjectIdAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='queries',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_queries_created',
    )
    message = models.TextField()
    response = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='PENDING_ADMIN_APPROVAL',
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'tenants_tenant_query'
        verbose_name = 'Tenant query'
        verbose_name_plural = 'Tenant queries'
        ordering = ['-created_at']

    def __str__(self):
        return f'Query {self.tenant_id} — {self.status}'
