# Tenant SUSPENDED status + TenantQuery model

import django.db.models.deletion
import django.utils.timezone
import django_mongodb_backend.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_backfill_default_tenant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenant',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                    ('SUSPENDED', 'Suspended'),
                ],
                db_index=True,
                default='PENDING',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='TenantQuery',
            fields=[
                (
                    'id',
                    django_mongodb_backend.fields.ObjectIdAutoField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('message', models.TextField()),
                ('response', models.TextField(blank=True, default='')),
                (
                    'status',
                    models.CharField(
                        choices=[('PENDING', 'Pending'), ('ANSWERED', 'Answered')],
                        db_index=True,
                        default='PENDING',
                        max_length=20,
                    ),
                ),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                (
                    'tenant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='queries',
                        to='tenants.tenant',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Tenant query',
                'verbose_name_plural': 'Tenant queries',
                'db_table': 'tenants_tenant_query',
                'ordering': ['-created_at'],
            },
        ),
    ]
