#!/usr/bin/env python
import os
import asyncio

import telegram.error
from telegram import Bot
from marto_python.secrets import read_secrets, get_secret
from db import BASE_DIR
from bot import try_send_today


async def main():
    read_secrets(base_dir=BASE_DIR)
    bot = Bot(token=get_secret('TELEGRAM_TOKEN'))
    group_id = get_secret('GROUP_ID')
    try:
        async with bot:
            await try_send_today(bot, group_id)
    except telegram.error.NetworkError as e:
        print('Network error - ', e)

if __name__ == '__main__':
    asyncio.run(main())