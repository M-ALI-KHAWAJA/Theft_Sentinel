import logging
import threading

from django.contrib.auth import get_user_model

from apps.accounts.validation import normalize_pakistani_phone
from apps.mobile.services import NotificationService

logger = logging.getLogger(__name__)


def is_theft_alert(alert) -> bool:
    alert_type = (getattr(alert, "alert_type", "") or "").lower()
    return "theft" in alert_type


def dispatch_theft_alert_sms(alert, async_send=True) -> bool:
    """
    Send the branch-admin SMS for a theft alert exactly once.

    The idempotency marker lives in alert.metadata so manual API alerts,
    surveillance events, and the continuous monitor all share the same guard.
    """
    if not alert or not is_theft_alert(alert):
        return False

    metadata = dict(getattr(alert, "metadata", None) or {})
    if metadata.get("twilio_sms_attempted"):
        logger.info("Skipping duplicate Twilio SMS for alert %s", alert.id)
        return False

    camera = getattr(alert, "camera_id", None)
    branch = getattr(camera, "branch", None)
    raw_phone = getattr(branch, "admin_phone", "") if branch else ""

    metadata["twilio_sms_attempted"] = True
    metadata["twilio_sms_status"] = "PENDING"

    try:
        phone = normalize_pakistani_phone(raw_phone, required=True)
    except Exception as exc:
        metadata["twilio_sms_status"] = "FAILED"
        metadata["twilio_sms_error"] = str(exc)
        alert.metadata = metadata
        alert.save(update_fields=["metadata"])
        logger.error("Twilio SMS skipped for alert %s: invalid branch admin phone %r", alert.id, raw_phone)
        return False

    User = get_user_model()
    branch_admin = User.objects.filter(role="ADMIN", branch=branch, is_active=True).first()
    if not branch_admin:
        metadata["twilio_sms_status"] = "FAILED"
        metadata["twilio_sms_error"] = "Active branch admin not found"
        alert.metadata = metadata
        alert.save(update_fields=["metadata"])
        logger.error("Twilio SMS skipped for alert %s: active branch admin not found", alert.id)
        return False

    metadata["twilio_sms_phone"] = phone
    alert.metadata = metadata
    alert.save(update_fields=["metadata"])
    logger.info("Twilio theft SMS target for alert %s: %s", alert.id, phone)

    message = (
        "Theft Sentinel Alert:\n"
        f"Potential theft detected at {getattr(branch, 'branch_name', 'Unknown branch')}\n"
        f"Camera: {getattr(camera, 'name', 'Unknown camera')}\n"
        f"Severity: {alert.severity}\n"
        f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    def _send():
        try:
            success = NotificationService.send_sms(branch_admin, phone, message)
            from apps.alerts.models import Alert

            fresh = Alert.objects.get(pk=alert.pk)
            fresh_metadata = dict(fresh.metadata or {})
            fresh_metadata["twilio_sms_status"] = "SENT" if success else "FAILED"
            fresh.metadata = fresh_metadata
            fresh.save(update_fields=["metadata"])
            if success:
                logger.info("Twilio theft SMS sent for alert %s to %s", alert.id, phone)
            else:
                logger.error("Twilio theft SMS failed for alert %s to %s", alert.id, phone)
        except Exception as exc:
            logger.error("Twilio theft SMS failed for alert %s to %s: %s", alert.id, phone, exc, exc_info=True)
            try:
                from apps.alerts.models import Alert

                fresh = Alert.objects.get(pk=alert.pk)
                fresh_metadata = dict(fresh.metadata or {})
                fresh_metadata["twilio_sms_status"] = "FAILED"
                fresh_metadata["twilio_sms_error"] = str(exc)
                fresh.metadata = fresh_metadata
                fresh.save(update_fields=["metadata"])
            except Exception:
                logger.exception("Failed to persist Twilio failure metadata for alert %s", alert.id)

    if async_send:
        threading.Thread(target=_send, daemon=True, name=f"twilio-alert-{alert.id}").start()
    else:
        _send()
    return True
