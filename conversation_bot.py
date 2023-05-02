#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
# pylint: disable=unused-argument, wrong-import-position

import django
django.setup()

import logging
from django.conf import settings
from telegram.ext import Application
from lessons import bot as bot_module
from lessons.bot_updates import configure_handlers

logger = logging.getLogger(__name__)


def main():
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    bot_module.bot = application.bot
    configure_handlers(application)
    application.run_polling()


if __name__ == '__main__':
    main()
