"""
Helpers for tenant-scoped querysets (branch isolation).
"""


def branch_tenant_id(user):
    """
    Returns tenant id for an approved branch user, or None for SUPER_ADMIN / invalid.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if getattr(user, 'role', None) == 'SUPER_ADMIN':
        return None
    tid = getattr(user, 'tenant_id', None)
    if not tid:
        return None
    tenant = getattr(user, 'tenant', None)
    if tenant is None:
        return None
    if tenant.status != 'APPROVED':
        return None
    return tid


def scoped_cameras(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.cameras.models import Camera

        return Camera.objects.none()
    from apps.cameras.models import Camera

    return Camera.objects.filter(tenant_id=tid)


def scoped_alerts(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.alerts.models import Alert

        return Alert.objects.none()
    from apps.alerts.models import Alert

    return Alert.objects.filter(tenant_id=tid)


def scoped_incidents(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.incidents.models import Incident

        return Incident.objects.none()
    from apps.incidents.models import Incident

    return Incident.objects.filter(tenant_id=tid)


def scoped_feedback(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.feedback.models import Feedback

        return Feedback.objects.none()
    from apps.feedback.models import Feedback

    return Feedback.objects.filter(tenant_id=tid)


def scoped_users(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.none()
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.filter(tenant_id=tid).exclude(role='SUPER_ADMIN')


def scoped_personnel(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.personnel.models import Personnel

        return Personnel.objects.none()
    from apps.personnel.models import Personnel

    return Personnel.objects.filter(user__tenant_id=tid)


def scoped_surveillance_events(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.surveillance.models import SurveillanceEvent

        return SurveillanceEvent.objects.none()
    from apps.surveillance.models import SurveillanceEvent

    return SurveillanceEvent.objects.filter(camera_id__tenant_id=tid)


def scoped_tracking_records(user):
    tid = branch_tenant_id(user)
    if tid is None:
        from apps.tracking.models import TrackingRecord

        return TrackingRecord.objects.none()
    from apps.tracking.models import TrackingRecord

    return TrackingRecord.objects.filter(camera_id__tenant_id=tid)


def scoped_notifications(user):
    """Notification rows are scoped via related user.tenant."""
    from apps.mobile.models import Notification

    tid = branch_tenant_id(user)
    if tid is None:
        return Notification.objects.none()
    if getattr(user, 'role', None) == 'ADMIN':
        return Notification.objects.filter(user__tenant_id=tid)
    return Notification.objects.filter(user=user)


def assert_same_tenant(user, obj_tenant_id, message='Access denied.'):
    """Raise PermissionError if branch user does not match object's tenant."""
    tid = branch_tenant_id(user)
    if tid is None:
        raise PermissionError(message)
    if obj_tenant_id is None or str(obj_tenant_id) != str(tid):
        raise PermissionError(message)
