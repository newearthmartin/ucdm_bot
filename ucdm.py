#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import django
django.setup()
import logging
import asyncio
import telegram.error
from lessons.bot import bot, initialize_bot, try_send_all, process_updates

logger = logging.getLogger(__name__)


async def main():
    try:
        bot = await initialize_bot(False)
        updates = await bot.get_updates()
        await process_updates(bot, updates)
        await try_send_all(bot)
    except telegram.error.NetworkError as e:
        logger.warning(f'Network error: {e}')
    except:
        logger.error('Unexpected exception', exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
