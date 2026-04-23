"""
Branch registration (public) and super-admin tenant management.
"""
import logging

from django.contrib.auth import get_user_model

from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Tenant, TenantQuery
from .serializers import (
    BranchRegisterSerializer,
    BranchTenantProfileSerializer,
    TenantListSerializer,
    TenantQueryAdminSerializer,
    TenantQueryAnswerSerializer,
    TenantQueryCreateSerializer,
    TenantQuerySerializer,
)
from apps.accounts.permissions import (
    IsAdmin,
    IsApprovedBranchUser,
    IsSuperAdmin,
    IsSuperAdminOrApprovedBranchUser,
)
from config.email_utils import send_system_mail

logger = logging.getLogger(__name__)
User = get_user_model()


class BranchRegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = BranchRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tenant, user = ser.save()
        return Response(
            {
                'message': 'Registration submitted. You will receive an email when your branch is approved.',
                'tenant_id': str(tenant.id),
            },
            status=status.HTTP_201_CREATED,
        )


class BranchTenantProfileView(views.APIView):
    """Approved branch users: read branch details; Admin may update CNIC and phone."""

    permission_classes = [IsAuthenticated, IsApprovedBranchUser]

    def get(self, request):
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response({'error': 'No branch assigned.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BranchTenantProfileSerializer(tenant).data)

    def patch(self, request):
        if getattr(request.user, 'role', None) != 'ADMIN':
            return Response(
                {'error': 'Only branch administrators can update CNIC and phone.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            return Response({'error': 'No branch assigned.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = BranchTenantProfileSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(BranchTenantProfileSerializer(tenant).data)


class SuperAdminTenantListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.all().order_by('-created_at')


class SuperAdminTenantDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.all()


class SuperAdminDashboardView(views.APIView):
    """Aggregate counts for platform operator (branches only)."""

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response(
            {
                'tenants_total': Tenant.objects.count(),
                'tenants_pending': Tenant.objects.filter(status='PENDING').count(),
                'tenants_approved': Tenant.objects.filter(status='APPROVED').count(),
                'tenants_rejected': Tenant.objects.filter(status='REJECTED').count(),
                'tenants_suspended': Tenant.objects.filter(status='SUSPENDED').count(),
                'queries_total': TenantQuery.objects.count(),
            }
        )


def _send_tenant_email(tenant, subject, body):
    try:
        send_system_mail(
            subject=subject,
            message=body,
            recipient_list=[tenant.email],
        )
    except Exception:
        logger.exception('Failed to send tenant email to %s', tenant.email)


class SuperAdminTenantApproveView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        if tenant.status != 'PENDING':
            return Response(
                {'error': 'Only pending registrations can be approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.status = 'APPROVED'
        tenant.save(update_fields=['status'])
        _send_tenant_email(
            tenant,
            'Branch Approved',
            'Your branch has been approved',
        )
        return Response(TenantListSerializer(tenant).data)


class SuperAdminTenantRejectView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        if tenant.status != 'PENDING':
            return Response(
                {'error': 'Only pending registrations can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.status = 'REJECTED'
        tenant.save(update_fields=['status'])
        User.objects.filter(tenant=tenant, role='ADMIN').update(is_active=False)
        _send_tenant_email(
            tenant,
            'Branch registration rejected',
            'Your branch registration was rejected.',
        )
        return Response(TenantListSerializer(tenant).data)


class SuperAdminTenantSuspendView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        if tenant.status != 'APPROVED':
            return Response(
                {'error': 'Only approved branches can be suspended.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.status = 'SUSPENDED'
        tenant.save(update_fields=['status'])
        _send_tenant_email(
            tenant,
            'Branch suspended',
            'Your branch has been suspended',
        )
        return Response(TenantListSerializer(tenant).data)


class SuperAdminTenantReapproveView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        if tenant.status != 'SUSPENDED':
            return Response(
                {'error': 'Only suspended branches can be re-approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.status = 'APPROVED'
        tenant.save(update_fields=['status'])
        _send_tenant_email(
            tenant,
            'Branch re-approved',
            'Your branch has been re-approved',
        )
        return Response(TenantListSerializer(tenant).data)


class SuperAdminTenantDeleteView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def delete(self, request, pk):
        try:
            tenant = Tenant.objects.get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            send_system_mail(
                subject='Branch Deletion Notice',
                message='Your branch will be deleted.',
                recipient_list=[tenant.email],
            )
        except Exception:
            logger.exception('Failed to send branch deletion email to %s', tenant.email)
            return Response(
                {'error': 'Email service is currently unavailable. Branch was not deleted.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        User.objects.filter(tenant=tenant).delete()
        tenant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TenantQueryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsApprovedBranchUser]

    def get_queryset(self):
        return (
            TenantQuery.objects.filter(tenant_id=self.request.user.tenant_id)
            .select_related('created_by')
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenantQueryCreateSerializer
        return TenantQuerySerializer

    def perform_create(self, serializer):
        user = self.request.user
        tenant = user.tenant
        if user.role in ('SECURITY_GUARD', 'SECURITY_INCHARGE'):
            serializer.save(
                tenant=tenant,
                created_by=user,
                status='PENDING_ADMIN_APPROVAL',
            )
        elif user.role == 'ADMIN':
            serializer.save(
                tenant=tenant,
                created_by=user,
                status='PENDING_SUPERADMIN',
            )
        else:
            serializer.save(tenant=tenant, created_by=user, status='PENDING_ADMIN_APPROVAL')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            TenantQuerySerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class SuperAdminTenantQueryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = TenantQueryAdminSerializer

    def get_queryset(self):
        return (
            TenantQuery.objects.filter(status='PENDING_SUPERADMIN')
            .select_related('tenant', 'created_by')
            .order_by('-created_at')
        )


class TenantQueryApproveView(views.APIView):
    """Branch Admin forwards guard/incharge query to platform (Super Admin queue)."""

    permission_classes = [IsAuthenticated, IsApprovedBranchUser, IsAdmin]

    def post(self, request, pk):
        try:
            q = TenantQuery.objects.select_related('tenant').get(pk=pk)
        except TenantQuery.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)
        if str(q.tenant_id) != str(request.user.tenant_id):
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)
        if q.status != 'PENDING_ADMIN_APPROVAL':
            return Response(
                {'error': 'Only queries awaiting branch admin approval can be approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        q.status = 'PENDING_SUPERADMIN'
        q.save(update_fields=['status'])
        return Response(TenantQuerySerializer(q).data)


class TenantQueryAnswerView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request, pk):
        try:
            q = TenantQuery.objects.select_related('tenant').get(pk=pk)
        except TenantQuery.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)
        if q.status != 'PENDING_SUPERADMIN':
            return Response(
                {'error': 'Only queries in the Super Admin queue can be answered.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = TenantQueryAnswerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        q.response = ser.validated_data['response']
        q.status = 'ANSWERED'
        q.save(update_fields=['response', 'status'])
        return Response(TenantQueryAdminSerializer(q).data)


class TenantQueryDestroyView(views.APIView):
    permission_classes = [IsAuthenticated, IsSuperAdminOrApprovedBranchUser]

    def delete(self, request, pk):
        try:
            q = TenantQuery.objects.get(pk=pk)
        except TenantQuery.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)
        if q.status != 'ANSWERED':
            return Response(
                {'error': 'Cannot delete unanswered query'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        if getattr(user, 'role', None) == 'SUPER_ADMIN':
            q.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not getattr(user, 'tenant_id', None) or str(q.tenant_id) != str(user.tenant_id):
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)
        if user.role not in ('ADMIN', 'SECURITY_GUARD', 'SECURITY_INCHARGE'):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        q.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
