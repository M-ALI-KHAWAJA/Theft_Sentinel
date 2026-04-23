"""
Main URL Configuration

"""
print("DASHBOARD URLS LOADED")

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.accounts.views import (
    CreateSuperAdminView,
    PasswordResetRequestCreateView,
    PasswordResetRequestDestroyView,
)
from apps.tenants.views import (
    TenantQueryAnswerView,
    TenantQueryApproveView,
    TenantQueryDestroyView,
    TenantQueryListCreateView,
)

urlpatterns = [
    path('api/password-reset-request/<str:pk>/', PasswordResetRequestDestroyView.as_view()),
    path('api/password-reset-request/', PasswordResetRequestCreateView.as_view()),
    path('api/queries/<str:pk>/answer/', TenantQueryAnswerView.as_view()),
    path('api/queries/<str:pk>/approve/', TenantQueryApproveView.as_view()),
    path('api/queries/<str:pk>/', TenantQueryDestroyView.as_view()),
    path('api/queries/', TenantQueryListCreateView.as_view()),
    path('api/create-super-admin/', CreateSuperAdminView.as_view()),
    # API endpoints
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/super-admin/', include('apps.tenants.super_admin_urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/personnel/', include('apps.personnel.urls')),
    path('api/cameras/', include('apps.cameras.urls')),
    path('api/surveillance/', include('apps.surveillance.urls')),
    path('api/tracking/', include('apps.tracking.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/mobile/', include('apps.mobile.urls')),
    path('api/incidents/', include('apps.incidents.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
    
    # AI Engine endpoints (NEW - ISOLATED)
    path('api/ai/', include('apps.ai_engine.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

