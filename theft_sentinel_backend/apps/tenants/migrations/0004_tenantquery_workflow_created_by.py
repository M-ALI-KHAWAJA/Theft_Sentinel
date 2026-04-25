# TenantQuery: created_by, expanded status, migrate legacy PENDING -> PENDING_SUPERADMIN

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def forwards_migrate_query_status(apps, schema_editor):
    TenantQuery = apps.get_model('tenants', 'TenantQuery')
    TenantQuery.objects.filter(status='PENDING').update(status='PENDING_SUPERADMIN')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0003_tenant_suspended_and_tenantquery'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenantquery',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tenant_queries_created',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='tenantquery',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING_ADMIN_APPROVAL', 'Pending admin approval'),
                    ('PENDING_SUPERADMIN', 'Pending super admin'),
                    ('ANSWERED', 'Answered'),
                    ('PENDING', 'Pending (legacy)'),
                ],
                db_index=True,
                default='PENDING_ADMIN_APPROVAL',
                max_length=32,
            ),
        ),
        migrations.RunPython(forwards_migrate_query_status, migrations.RunPython.noop),
    ]
