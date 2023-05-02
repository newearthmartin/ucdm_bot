import logging
from django.conf import settings
from telegram import Bot, BotCommand, Update
from telegram.constants import ChatType, ChatMemberStatus, ParseMode
from datetime import datetime
from .workbook import get_day_texts, get_day_lesson_number
from .models import Chat

logger = logging.getLogger(__name__)

bot = None


async def initialize_bot():
    global bot
    if not bot:
        logger.info('Initializing bot')
        bot = Bot(token=settings.TELEGRAM_TOKEN)
        await bot.initialize()
        logger.info(f'Bot: {bot.username}')
        await set_commands()
    return bot


async def set_commands():
    logger.info('Setting bot commands')
    commands = [
        BotCommand('start', 'Comenzar a recibir las lecciones'),
        BotCommand('modo', 'Configurar el modo de las lecciones (calendario o propia)'),
        BotCommand('stop', 'Dejar de recibir las lecciones'),
    ]
    await bot.set_my_commands(commands)


async def set_chat_status(chat_id, send_lesson, is_group=False, send_msg=True):
    modified = await __modify_chat_status(chat_id, is_group, send_lesson)
    if modified and send_msg:
        if send_lesson:
            msg = 'Hola!\n\nA partir de ahora voy a estar mandando las lecciones todos los días.\n\n' \
                  'Para frenar las lecciones manda el mensaje */stop*'
        else:
            msg = 'Ya no enviaré las lecciones.\n\nPara volver a recibirlas, manda el mensaje */start*'
        await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN)


async def __modify_chat_status(chat_id, is_group, send_lesson):
    chat = await Chat.objects.filter(chat_id=chat_id).afirst()
    modified = False
    if not chat:
        if not send_lesson: return False
        chat = Chat(chat_id=chat_id, is_group=is_group, send_lesson=True)
        modified = True
    elif chat.send_lesson != send_lesson:
        chat.send_lesson = send_lesson
        modified = True
    if modified:
        action = 'send' if send_lesson else 'NOT send'
        logger.info(f'Setting {chat} to {action} lessons')
        await chat.asave()
    return modified


async def try_send_all():
    chats = Chat.objects.filter(send_lesson=True)
    chat_count = await chats.acount()
    logger.info(f'Sending to {chat_count} chats')
    async for chat in Chat.objects.filter(send_lesson=True).all():
        await try_send_today(chat)


async def try_send_today(chat):
    now = datetime.now()
    today = now.date()
    if not can_send_today(today, chat):
        logger.info(f'Already sent today\'s lesson to {chat}')
        return
    if now.hour < 8:
        logger.info(f'Too early to send to {chat}')
        return
    if now.hour >= 23:
        logger.info(f'Too late to send to {chat}')
        return
    lesson_number = get_day_lesson_number(today)
    if lesson_number is None:
        logger.warning(f'No lesson for {today}')
        return
    await send_lesson(chat, today, lesson_number)


def can_send_today(today, chat):
    if not chat.last_sent:
        return True
    return (today - chat.last_sent).days >= 1


async def send_lesson(chat, today, lesson_number):
    logger.info(f'Sending day {lesson_number} to {chat}')
    for text in get_day_texts(lesson_number):
        await __send_lesson_text(chat.chat_id, text)
    chat.last_sent = today
    chat.last_lesson_sent = lesson_number
    await chat.asave()


async def __send_lesson_text(chat_id, text):
    messages = split_for_telegram(text)
    if len(messages) > 1:
        part_lengths = [len(message) for message in messages]
        logger.info(f'Splitting message of length {len(text)} into {len(messages)} parts of lengths {part_lengths}')
    else:
        logger.info(f'Sending message of length {len(text)}')
    for message in messages:
        await bot.send_message(chat_id, message, parse_mode=ParseMode.MARKDOWN)


def split_for_telegram(text):
    parts = []
    lines = text.split('\n')
    part_len = 0
    part = []
    for line in lines:
        new_len = part_len + len(line) + (1 if part_len else 0)
        if new_len <= 4096:
            part.append(line)
        else:
            parts.append('\n'.join(part))
            part = [line]
            new_len = len(line)
        part_len = new_len
    if len(part) > 0:
        parts.append('\n'.join(part))
    return parts
