# Add optional branch phone number for tenant contact.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_tenantquery_workflow_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='phone',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
    ]
