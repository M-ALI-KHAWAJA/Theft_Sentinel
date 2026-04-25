# PasswordResetRequest + SuperAdminProfile
# MongoDB: skip create_collection when the collection already exists (e.g. partial prior run).

import django.db.models.deletion
import django.utils.timezone
import django_mongodb_backend.fields
from django.db import migrations, models


def create_collections_if_needed(apps, schema_editor):
    """
    RunPython receives ``from_state.apps`` (before state_operations), so new models
    are not importable here. Create Mongo collections by name only when missing.
    """
    db = schema_editor.connection.get_database()
    existing = set(db.list_collection_names())
    for table in ('accounts_password_reset_request', 'accounts_super_admin_profile'):
        if table not in existing:
            db.create_collection(table)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_multi_tenant'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='PasswordResetRequest',
                    fields=[
                        (
                            'id',
                            django_mongodb_backend.fields.ObjectIdAutoField(
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ('reason', models.TextField()),
                        (
                            'status',
                            models.CharField(
                                choices=[
                                    ('PENDING', 'Pending'),
                                    ('APPROVED', 'Approved'),
                                    ('REJECTED', 'Rejected'),
                                ],
                                db_index=True,
                                default='PENDING',
                                max_length=20,
                            ),
                        ),
                        ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                        (
                            'user',
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='password_reset_requests',
                                to='accounts.user',
                            ),
                        ),
                    ],
                    options={
                        'verbose_name': 'Password Reset Request',
                        'verbose_name_plural': 'Password Reset Requests',
                        'db_table': 'accounts_password_reset_request',
                        'ordering': ['-created_at'],
                    },
                ),
                migrations.CreateModel(
                    name='SuperAdminProfile',
                    fields=[
                        (
                            'id',
                            django_mongodb_backend.fields.ObjectIdAutoField(
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ('display_name', models.CharField(max_length=255)),
                        ('phone', models.CharField(max_length=32)),
                        ('partners', models.JSONField(blank=True, default=list)),
                        ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                        (
                            'user',
                            models.OneToOneField(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name='super_admin_profile',
                                to='accounts.user',
                            ),
                        ),
                    ],
                    options={
                        'verbose_name': 'Super Admin Profile',
                        'verbose_name_plural': 'Super Admin Profiles',
                        'db_table': 'accounts_super_admin_profile',
                    },
                ),
            ],
            database_operations=[
                migrations.RunPython(create_collections_if_needed, noop_reverse),
            ],
        ),
    ]
