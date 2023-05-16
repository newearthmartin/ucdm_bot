#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import django
django.setup()

import logging
import asyncio
from lessons.bot import initialize_bot, try_send_all
logger = logging.getLogger(__name__)


async def main():
    application = await initialize_bot()
    await application.updater.start_polling()
    await application.start()
    await send_all_loop()


async def send_all_loop():
    DELAY = 5 * 60
    logger.info(f'Starting send_all loop with delay {DELAY / 60} minutes')
    while True:
        try:
            await try_send_all()
        except Exception as e:
            logger.exception(e)
        await asyncio.sleep(DELAY)


if __name__ == '__main__':
    asyncio.run(main())
