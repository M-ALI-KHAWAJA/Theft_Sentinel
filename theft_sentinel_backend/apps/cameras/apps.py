from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CamerasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cameras'

    def ready(self):
        """
        Register runtime cleanup and start the feed health scheduler in the
        HTTP-serving process.
        """
        import atexit
        import apps.cameras.signals  # noqa: F401
        from .health_scheduler import health_scheduler, should_start_health_scheduler
        from .stream_manager import stream_manager

        def _shutdown():
            logger.info("[CamerasConfig] Server shutting down; stopping camera services")
            health_scheduler.stop()
            stream_manager.stop_all()
            logger.info("[CamerasConfig] Camera services stopped")

        atexit.register(_shutdown)
        logger.info("[CamerasConfig] Camera runtime cleanup registered")

        if should_start_health_scheduler():
            health_scheduler.start(interval=5)
        else:
            logger.info("[CamerasConfig] Camera feed health scheduler not started in this process")
