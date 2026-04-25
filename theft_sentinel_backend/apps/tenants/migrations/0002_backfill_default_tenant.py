# Data migration: legacy single-branch data → default approved tenant

from django.db import migrations


def forwards(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    User = apps.get_model('accounts', 'User')
    Camera = apps.get_model('cameras', 'Camera')
    Alert = apps.get_model('alerts', 'Alert')
    Incident = apps.get_model('incidents', 'Incident')
    Feedback = apps.get_model('feedback', 'Feedback')

    t = Tenant.objects.filter(email='legacy-default@theft-sentinel.local').first()
    if not t:
        t = Tenant.objects.create(
            name='Default Branch',
            email='legacy-default@theft-sentinel.local',
            cnic='00000-0000000-0',
            status='APPROVED',
        )

    for u in User.objects.filter(is_superuser=True):
        if getattr(u, 'role', None) != 'SUPER_ADMIN':
            u.role = 'SUPER_ADMIN'
        u.tenant = None
        u.save()

    for u in User.objects.exclude(role='SUPER_ADMIN').filter(tenant__isnull=True):
        u.tenant = t
        u.save()

    for c in Camera.objects.filter(tenant__isnull=True):
        c.tenant = t
        c.save()

    for a in Alert.objects.filter(tenant__isnull=True):
        cam_id = getattr(a, 'camera_id_id', None)
        if cam_id:
            cam = Camera.objects.filter(pk=cam_id).first()
            if cam and getattr(cam, 'tenant_id', None):
                a.tenant_id = cam.tenant_id
                a.save()
                continue
        a.tenant = t
        a.save()

    for i in Incident.objects.filter(tenant__isnull=True):
        aid = getattr(i, 'alert_id_id', None)
        if aid:
            al = Alert.objects.filter(pk=aid).first()
            if al and getattr(al, 'tenant_id', None):
                i.tenant_id = al.tenant_id
                i.save()
                continue
        i.tenant = t
        i.save()

    for f in Feedback.objects.filter(tenant__isnull=True):
        uid = getattr(f, 'user_id_id', None)
        if uid:
            user = User.objects.filter(pk=uid).first()
            if user and getattr(user, 'tenant_id', None):
                f.tenant_id = user.tenant_id
                f.save()
                continue
        f.tenant = t
        f.save()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_multi_tenant'),
        ('accounts', '0004_multi_tenant'),
        ('cameras', '0003_multi_tenant'),
        ('alerts', '0004_multi_tenant'),
        ('incidents', '0003_multi_tenant'),
        ('feedback', '0002_multi_tenant'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
