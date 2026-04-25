from django.urls import path

from apps.accounts.views import (
    SuperAdminDeleteAccountView,
    SuperAdminPasswordResetRequestApproveView,
    SuperAdminPasswordResetRequestListView,
    SuperAdminPasswordResetRequestRejectView,
    SuperAdminProfileView,
    SuperAdminSelfPasswordResetView,
)
from .views import (
    SuperAdminDashboardView,
    SuperAdminTenantListView,
    SuperAdminTenantDetailView,
    SuperAdminTenantApproveView,
    SuperAdminTenantRejectView,
    SuperAdminTenantDeleteView,
    SuperAdminTenantReapproveView,
    SuperAdminTenantSuspendView,
    SuperAdminTenantQueryListView,
)

urlpatterns = [
    path('dashboard/', SuperAdminDashboardView.as_view(), name='super_admin_dashboard'),
    path('reset-password/', SuperAdminSelfPasswordResetView.as_view(), name='super_admin_self_reset_password'),
    path('delete-account/', SuperAdminDeleteAccountView.as_view(), name='super_admin_delete_account'),
    path('profile/', SuperAdminProfileView.as_view(), name='super_admin_profile'),
    path('queries/', SuperAdminTenantQueryListView.as_view(), name='super_admin_tenant_queries'),
    path('tenants/', SuperAdminTenantListView.as_view(), name='super_admin_tenant_list'),
    path('tenants/<str:pk>/delete/', SuperAdminTenantDeleteView.as_view(), name='super_admin_tenant_delete'),
    path('tenants/<str:pk>/suspend/', SuperAdminTenantSuspendView.as_view(), name='super_admin_tenant_suspend'),
    path('tenants/<str:pk>/re-approve/', SuperAdminTenantReapproveView.as_view(), name='super_admin_tenant_reapprove'),
    path('tenants/<str:pk>/approve/', SuperAdminTenantApproveView.as_view(), name='super_admin_tenant_approve'),
    path('tenants/<str:pk>/reject/', SuperAdminTenantRejectView.as_view(), name='super_admin_tenant_reject'),
    path('tenants/<str:pk>/', SuperAdminTenantDetailView.as_view(), name='super_admin_tenant_detail'),
    path(
        'password-reset-requests/',
        SuperAdminPasswordResetRequestListView.as_view(),
        name='super_admin_password_reset_requests',
    ),
    path(
        'password-reset-requests/<str:pk>/approve/',
        SuperAdminPasswordResetRequestApproveView.as_view(),
        name='super_admin_password_reset_request_approve',
    ),
    path(
        'password-reset-requests/<str:pk>/reject/',
        SuperAdminPasswordResetRequestRejectView.as_view(),
        name='super_admin_password_reset_request_reject',
    ),
]
