#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import asyncio
import django
django.setup()

from lessons.bot_loop import run_bot_loop

if __name__ == '__main__':
    asyncio.run(run_bot_loop())
