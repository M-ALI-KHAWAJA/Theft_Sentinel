"""
Views for Authentication and User Management
"""
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
import logging

from rest_framework.serializers import ValidationError as DRFValidationError

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    PasswordResetRequestCreateSerializer,
    PasswordResetRequestReadSerializer,
    CreateSuperAdminSerializer,
    SuperAdminProfileSerializer,
    validate_password_strength,
)
from .permissions import (
    IsAdmin,
    CanChangeOwnPassword,
    CanManageUsers,
    IsAdminOrIncharge,
    IsApprovedBranchUser,
    IsSuperAdmin,
)
from .models import (
    PasswordResetToken,
    PasswordResetAudit,
    PasswordResetRequest,
    SuperAdminProfile,
)
from config.env_validator import get_client_ip, get_user_agent
from config.email_utils import send_system_mail

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    ADMIN-ONLY User Creation Endpoint
    
    This view is NOT publicly accessible. Only authenticated Admin users
    with CanManageUsers permission can create new users.
    
    Public self-registration has been disabled. All user accounts must be
    created by administrators through the admin panel or user management interface.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanManageUsers]
    serializer_class = UserCreateSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User created successfully by admin'
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with user data"""
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(views.APIView):
    """Logout view - blacklist refresh token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update current user profile"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(views.APIView):
    """
    Change password for current user
    All users can change their own password
    """
    permission_classes = [IsAuthenticated, CanChangeOwnPassword]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {'error': 'Wrong old password'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    List all users (Admin and Security In-Charge can view)
    Admin and Security In-Charge need to list guards for assignment
    Full CRUD operations (create/update/delete) remain Admin-only
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdminOrIncharge]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
    
    def get_queryset(self):
        queryset = User.objects.filter(tenant_id=self.request.user.tenant_id).exclude(
            role='SUPER_ADMIN'
        )
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        return queryset.order_by('-created_at')


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete user (Admin only)
    Full CRUD on users is Admin-only permission
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, CanManageUsers]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def get_queryset(self):
        return User.objects.filter(tenant_id=self.request.user.tenant_id).exclude(role='SUPER_ADMIN')
    
    def update(self, request, *args, **kwargs):
        """Override update to enforce Admin uniqueness"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if trying to set role to ADMIN
        if 'role' in request.data and request.data['role'] == 'ADMIN':
            # Check if another Admin already exists (excluding current user)
            existing_admin = (
                User.objects.filter(
                    role='ADMIN',
                    is_active=True,
                    tenant_id=request.user.tenant_id,
                )
                .exclude(pk=instance.pk)
                .first()
            )
            if existing_admin:
                return Response(
                    {'role': ['Only one Admin can exist per branch. An Admin user already exists.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to enforce Admin uniqueness"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'ADMIN' and instance.pk == request.user.pk:
            return Response(
                {'error': 'Admin cannot delete their own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class AdminChangeUserPasswordView(views.APIView):
    """
    Admin can change any user's password
    Only Admin has this permission
    """
    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdmin]
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, tenant_id=request.user.tenant_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password_strength(new_password)
        except DRFValidationError as exc:
            detail = exc.detail
            msg = str(detail[0]) if isinstance(detail, list) and detail else str(detail)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': f'Password changed successfully for user {user.username}'
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(views.APIView):
    """
    Legacy direct forgot-password endpoint (disabled).

    Password reset links are issued only after a Super Admin approves a
    ``PasswordResetRequest`` (see ``POST /api/password-reset-request/``).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        return Response(
            {
                'error': (
                    'Direct password reset is disabled. Use the password reset request form; '
                    'a Super Admin must approve your request before a reset link is emailed.'
                )
            },
            status=status.HTTP_403_FORBIDDEN,
        )


class ResetPasswordView(views.APIView):
    """
    Reset password using a token issued after Super Admin approval.

    Validates the reset token, enforces expiry, updates the user's password,
    marks the token used, and writes audit rows.
    """

    permission_classes = [AllowAny]
    
    def _log_audit(self, email, is_admin, success, reason, request):
        """Log password reset attempt for audit purposes"""
        try:
            PasswordResetAudit.objects.create(
                email=email,
                is_admin=is_admin,
                success=success,
                reason=reason,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
            )
        except Exception as e:
            # Don't fail the request if audit logging fails
            logger.error(f"Failed to log password reset audit: {str(e)}", exc_info=True)
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Log validation failure
            token = request.data.get('token', 'unknown')
            self._log_audit(
                email='unknown',
                is_admin=False,
                success=False,
                reason='Invalid reset data (validation failed)',
                request=request
            )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token_value = (serializer.validated_data['token'] or '').strip()
        new_password = serializer.validated_data['new_password']

        try:
            reset_token = PasswordResetToken.objects.get(token=token_value)
            user = reset_token.user
            user_email = user.email if user else 'unknown'
            
            # Check if token is valid
            if not reset_token.is_valid():
                if reset_token.used:
                    # Log used token attempt
                    self._log_audit(
                        email=user_email,
                        is_admin=user.role in ('ADMIN', 'SUPER_ADMIN') if user else False,
                        success=False,
                        reason='Token already used',
                        request=request
                    )
                    return Response(
                        {'error': 'This reset link has already been used. Please request a new one.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                elif reset_token.is_expired():
                    # Log expired token attempt
                    self._log_audit(
                        email=user_email,
                        is_admin=user.role in ('ADMIN', 'SUPER_ADMIN') if user else False,
                        success=False,
                        reason='Token expired',
                        request=request
                    )
                    return Response(
                        {'error': 'This reset link has expired. Please request a new one.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.used = True
            reset_token.save()
            
            logger.info('Password reset successful for user_id=%s', user.pk)

            # Log successful password reset
            self._log_audit(
                email=user_email,
                is_admin=user.role in ('ADMIN', 'SUPER_ADMIN'),
                success=True,
                reason='Password successfully reset',
                request=request,
            )
            
            return Response(
                {'message': 'Password successfully updated. You may now log in.'},
                status=status.HTTP_200_OK
            )
            
        except PasswordResetToken.DoesNotExist:
            # Log invalid token attempt
            self._log_audit(
                email='unknown',
                is_admin=False,
                success=False,
                reason='Invalid or non-existent token',
                request=request
            )
            return Response(
                {'error': 'Invalid or expired reset token. Please request a new password reset.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestCreateView(views.APIView):
    """Public: submit a reset request for Super Admin review."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.context['resolved_user']
        if PasswordResetRequest.objects.filter(user=user, status='PENDING').exists():
            return Response(
                {'error': 'You already have a pending password reset request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pr = PasswordResetRequest.objects.create(
            user=user,
            reason=serializer.validated_data['reason'],
            status='PENDING',
        )
        logger.info(
            'password_reset_request_created id=%s user_id=%s email=%s tenant_id=%s',
            pr.pk,
            user.pk,
            user.email,
            getattr(user, 'tenant_id', None),
        )
        return Response(
            {'message': 'Request sent to Super Admin'},
            status=status.HTTP_201_CREATED,
        )


class CreateSuperAdminView(views.APIView):
    """One-time bootstrap: create the platform Super Admin if none exists."""

    permission_classes = [AllowAny]

    def get(self, request):
        can_create = not User.objects.filter(role='SUPER_ADMIN').exists()
        return Response({'can_create': can_create})

    def post(self, request):
        if User.objects.filter(role='SUPER_ADMIN').exists():
            return Response(
                {'error': 'Super Admin already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CreateSuperAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data['email']
        base_username = email.split('@')[0].replace('.', '_')[:120]
        username = base_username
        n = 0
        while User.objects.filter(username=username, tenant__isnull=True).exists():
            n += 1
            username = f'{base_username}_{n}'[:150]

        user = User.objects.create_user(
            email,
            data['password'],
            username=username,
            role='SUPER_ADMIN',
            tenant=None,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        SuperAdminProfile.objects.create(
            user=user,
            display_name=data['name'],
            phone=data['phone'],
            partners=list(data['partners']),
        )
        return Response(
            {
                'message': 'Super Admin created successfully.',
                'user_id': str(user.pk),
            },
            status=status.HTTP_201_CREATED,
        )


class SuperAdminPasswordResetRequestListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = PasswordResetRequestReadSerializer
    queryset = PasswordResetRequest.objects.all().order_by('-created_at')


class SuperAdminPasswordResetRequestApproveView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            reset_request = PasswordResetRequest.objects.get(pk=pk)
        except PasswordResetRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        if reset_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending requests can be approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = reset_request.user
        token = PasswordResetToken.generate_token()
        expires_at = timezone.now() + timedelta(minutes=30)
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at,
        )
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        # Query-string link survives email clients better than a long path segment.
        reset_link = f'{frontend_url}/reset-password?token={token}'
        try:
            send_system_mail(
                subject='Password Reset Approved',
                message=f'Reset your password: {reset_link}',
                recipient_list=[user.email],
            )
        except Exception:
            logger.exception(
                'Failed to send password reset approval email to user_id=%s',
                user.pk,
            )
            try:
                reset_token.delete()
            except Exception:
                logger.exception('Failed to roll back reset token after email error')
            return Response(
                {'error': 'Email service is currently unavailable. Please try again later.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        reset_request.status = 'APPROVED'
        reset_request.save(update_fields=['status'])
        return Response(PasswordResetRequestReadSerializer(reset_request).data)


class SuperAdminPasswordResetRequestRejectView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            reset_request = PasswordResetRequest.objects.get(pk=pk)
        except PasswordResetRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        if reset_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending requests can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reset_request.status = 'REJECTED'
        reset_request.save(update_fields=['status'])
        try:
            send_system_mail(
                subject='Password reset request declined',
                message=(
                    'Your password reset request was not approved. '
                    'Contact your administrator if you still need access.'
                ),
                recipient_list=[reset_request.user.email],
            )
        except Exception:
            logger.exception(
                'Failed to send password reset rejection email to user_id=%s',
                reset_request.user_id,
            )
        return Response(PasswordResetRequestReadSerializer(reset_request).data)


class SuperAdminSelfPasswordResetView(views.APIView):
    """
    Super Admin password reset email (no reason, no approval queue).

    - Authenticated Super Admin: uses current user (optional for profile UI).
    - Unauthenticated: JSON ``{"email": "..."}`` must match an active Super Admin account.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        def issue_and_email(user):
            from_email = getattr(settings, 'EMAIL_HOST_USER', '') or ''
            logger.info(
                'super_admin_reset: preparing token user_id=%s recipient_email=%s from_email_set=%s',
                user.pk,
                user.email,
                bool(from_email),
            )
            if not from_email:
                logger.error('super_admin_reset: EMAIL_HOST_USER is empty; cannot send mail')
                return Response(
                    {'error': 'Email service is not configured. Please try again later.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            token = PasswordResetToken.generate_token()
            expires_at = timezone.now() + timedelta(minutes=30)
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at,
            )
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
            reset_link = f'{frontend_url}/reset-password/{token}'
            subject = 'Super Admin Password Reset'
            body = f'Reset your password: {reset_link}'
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=from_email,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info(
                    'super_admin_reset: send_mail succeeded user_id=%s to=%s',
                    user.pk,
                    user.email,
                )
            except Exception:
                logger.exception(
                    'super_admin_reset: send_mail failed user_id=%s to=%s',
                    user.pk,
                    user.email,
                )
                try:
                    reset_token.delete()
                except Exception:
                    logger.exception('Failed to roll back reset token after email error')
                return Response(
                    {'error': 'Email service is currently unavailable. Please try again later.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response({'message': 'Reset link sent'})

        u = getattr(request, 'user', None)
        if u and u.is_authenticated and getattr(u, 'role', None) == 'SUPER_ADMIN':
            return issue_and_email(u)

        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if '@' not in email:
            return Response({'error': 'Enter a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

        target = User.objects.filter(email__iexact=email).first()
        if not target or target.role != 'SUPER_ADMIN' or not target.is_active:
            return Response(
                {'error': 'Invalid Super Admin email'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return issue_and_email(target)


class SuperAdminDeleteAccountView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def delete(self, request):
        from apps.tenants.models import Tenant

        if Tenant.objects.exists():
            return Response(
                {'error': 'Delete all branches before deleting Super Admin'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        user.delete()
        return Response(
            {
                'message': 'Super Admin account deleted.',
                'clear_tokens': True,
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminProfileView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        profile = SuperAdminProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response(
                {'error': 'Super Admin profile not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SuperAdminProfileSerializer(profile).data)

    def patch(self, request):
        profile = SuperAdminProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response(
                {'error': 'Super Admin profile not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SuperAdminProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile.refresh_from_db()
        return Response(SuperAdminProfileSerializer(profile).data)


class PasswordResetRequestDestroyView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def delete(self, request, pk):
        try:
            obj = PasswordResetRequest.objects.get(pk=pk)
        except PasswordResetRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        if obj.status == 'PENDING':
            return Response(
                {'error': 'Cannot delete a pending request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
