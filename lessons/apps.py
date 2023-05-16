import os
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class LessonsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lessons'

    def ready(self):
        if not os.environ.get('RUN_MAIN'):  # To prevent double running
            return

        import asyncio
        from threading import Thread
        from .bot_loop import run_bot_loop

        Thread(target=lambda: asyncio.run(run_bot_loop())).start()


