"""
User Model with Role-Based Access Control
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django_mongodb_backend.fields import ObjectIdAutoField
import secrets


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model with role-based access"""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('SECURITY_INCHARGE', 'Security In-Charge'),
        ('SECURITY_GUARD', 'Security Guard'),
    ]
    
    id = ObjectIdAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='SECURITY_GUARD')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    @property
    def is_security_incharge(self):
        return self.role == 'SECURITY_INCHARGE'
    
    @property
    def is_security_guard(self):
        return self.role == 'SECURITY_GUARD'


class PasswordResetToken(models.Model):
    """
    Password reset token model for admin-only password reset flow
    Tokens expire after 30 minutes
    """
    id = ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'accounts_password_reset_token'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email} (expires: {self.expires_at})"
    
    def is_expired(self):
        """Check if token has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.used and not self.is_expired()
    
    @staticmethod
    def generate_token():
        """Generate a secure random token (32 characters)"""
        return secrets.token_urlsafe(32)


class PasswordResetAudit(models.Model):
    """
    Audit log model for password reset attempts
    Tracks all password reset requests for security auditing
    """
    id = ObjectIdAutoField(primary_key=True)
    email = models.EmailField(db_index=True)
    is_admin = models.BooleanField(default=False, db_index=True)
    success = models.BooleanField(default=False, db_index=True)
    reason = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'accounts_password_reset_audit'
        verbose_name = 'Password Reset Audit'
        verbose_name_plural = 'Password Reset Audits'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['email', '-timestamp']),
            models.Index(fields=['is_admin', 'success', '-timestamp']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"Password reset {status} - {self.email} at {self.timestamp}"
