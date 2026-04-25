"""
Centralized outbound email: always from the system SMTP identity (EMAIL_HOST_USER).
Recipients are always dynamic (user/tenant addresses from the database).
"""
from django.conf import settings
from django.core.mail import send_mail


def send_system_mail(subject, message, recipient_list, *, fail_silently=False):
    """
    Send one message using the single configured system sender.

    from_email is always settings.EMAIL_HOST_USER (never per-tenant SMTP).
    """
    sender = getattr(settings, 'EMAIL_HOST_USER', '') or ''
    if not sender:
        raise ValueError('EMAIL_HOST_USER is not configured.')
    if not recipient_list:
        raise ValueError('recipient_list cannot be empty.')
    return send_mail(
        subject=subject,
        message=message,
        from_email=sender,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
    )
