#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import django
django.setup()
import asyncio
import telegram
from django.conf import settings
from lessons.bot import try_send_all, get_updates


async def main():
    bot = telegram.Bot(token=settings.TELEGRAM_TOKEN)
    try:
        async with bot:
            await get_updates(bot)
            await try_send_all(bot)
    except telegram.error.NetworkError as e:
        print('Network error - ', e)

if __name__ == '__main__':
    asyncio.run(main())
