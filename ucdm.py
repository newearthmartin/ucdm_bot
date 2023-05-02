#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
import django
django.setup()

import logging
import asyncio
from telegram.ext import Updater
from telegram.error import NetworkError
from lessons.bot import initialize_bot, try_send_all, process_update
logger = logging.getLogger(__name__)


async def main():
    while True:
        try:
            bot = await initialize_bot()
            await asyncio.gather(process_updates_loop(bot), send_all_loop(bot))
        except asyncio.exceptions.CancelledError:
            return
        except NetworkError as e:
            logger.info('Exiting')
            logger.warning(f'Network error: {e}')
        except:
            logger.error('Unexpected exception', exc_info=True)
        logger.info('Sleeping for 30 seconds')
        await asyncio.sleep(30)


async def process_updates_loop(bot):
    queue = asyncio.Queue()
    updater = Updater(bot, update_queue=queue)
    logger.info('Starting Updater polling')
    await updater.initialize()
    await updater.start_polling()
    logger.info('Starting update loop')
    while True:
        update = await queue.get()
        await process_update(update)


async def send_all_loop(bot):
    DELAY = 5 * 60
    logger.info(f'Starting send_all loop with delay {DELAY / 60} minutes')
    while True:
        await try_send_all()
        await asyncio.sleep(DELAY)


if __name__ == '__main__':
    asyncio.run(main())
