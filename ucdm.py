#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import django
django.setup()

from django.conf import settings
import asyncio
import telegram.error
from telegram import Bot
from lessons.bot import try_send_all, get_updates


async def main():
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    try:
        async with bot:
            await get_updates(bot)
            await try_send_all(bot)
    except telegram.error.NetworkError as e:
        print('Network error - ', e)

if __name__ == '__main__':
    asyncio.run(main())
