#!/usr/bin/env python
import asyncio
from telegram import Bot
from marto_python.secrets import read_secrets, get_secret
from bot import send_day


async def main():
    read_secrets('.')
    bot = Bot(token=get_secret('TELEGRAM_TOKEN'))
    group_id = get_secret('GROUP_ID')
    async with bot:
        await send_day(bot, group_id, 0)


if __name__ == '__main__':
    asyncio.run(main())