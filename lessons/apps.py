import logging
import os
from django.apps import AppConfig
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class LessonsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lessons'

    def ready(self):
        if not os.environ.get('RUN_MAIN'):  # To prevent double running
            return
        from .bot import initialize_bot
        async_to_sync(initialize_bot)(True)
