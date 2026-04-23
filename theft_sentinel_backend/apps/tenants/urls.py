from django.urls import path

from .views import BranchRegisterView, BranchTenantProfileView

urlpatterns = [
    path('register/', BranchRegisterView.as_view(), name='branch_register'),
    path('branch-profile/', BranchTenantProfileView.as_view(), name='branch_tenant_profile'),
]
