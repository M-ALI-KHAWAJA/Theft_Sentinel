# Allow same username on different tenants (per-branch uniqueness enforced in serializers).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_passwordresetrequest_superadminprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(db_index=True, max_length=150),
        ),
    ]
