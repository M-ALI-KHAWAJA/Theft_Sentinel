import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Camera
from .services import cleanup_camera_runtime

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Camera)
def cleanup_camera_runtime_before_delete(sender, instance, **kwargs):
    camera_id = str(instance.id)
    logger.info(
        "[cleanup] Camera %s (%s) is being deleted; stopping runtime resources",
        instance.name,
        camera_id,
    )
    cleanup_camera_runtime(camera_id)
