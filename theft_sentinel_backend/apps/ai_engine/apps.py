"""
AI Engine App Configuration
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AiEngineConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'apps.ai_engine'
    verbose_name = 'AI Engine'
    
    def ready(self):
        """
        Initialize AI service when Django starts
        """
        # Only initialize in main process (not in migrations, etc.)
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                logger.info("🚀 Initializing AI Engine...")
                from apps.ai_engine.services import ai_service
                ai_service.initialize()
                logger.info("✅ AI Engine initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize AI Engine: {str(e)}")
                # Don't crash the server, just log the error
                logger.warning("⚠️ Server will run without AI capabilities")
