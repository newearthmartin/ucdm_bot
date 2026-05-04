import logging
import asyncio
from telegram.error import NetworkError, TelegramError
from lessons.bot_updates import initialize_bot
from lessons.bot import try_send_all

logger = logging.getLogger(__name__)


async def run_bot_loop():
    application = await initialize_bot()
    await application.updater.start_polling(error_callback=polling_error_callback)
    await application.start()
    await send_all_loop()


def polling_error_callback(error: TelegramError):
    if isinstance(error, NetworkError):
        logger.warning(f'Telegram polling network error: {error}')
    else:
        logger.exception('Exception happened while polling for updates.')


async def send_all_loop():
    DELAY = 5 * 60
    logger.info(f'Starting send_all loop with delay {DELAY / 60} minutes')
    while True:
        try:
            await try_send_all()
        except Exception as e:
            logger.exception(e)
        await asyncio.sleep(DELAY)
