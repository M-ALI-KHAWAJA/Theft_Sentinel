from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'cnic', 'status', 'created_at')
    list_filter = ('status',)
