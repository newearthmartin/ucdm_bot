import asyncio
import logging
from django.conf import settings
from telegram import BotCommand
from telegram.constants import ParseMode
from telegram.ext import Application
from datetime import datetime
from .workbook import get_day_texts, get_day_lesson_number
from .models import Chat
from . import bot_updates

logger = logging.getLogger(__name__)

bot = None
application = None


async def initialize_bot():
    global bot
    global application
    if not bot:
        logger.info('Initializing bot')
        application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
        bot_updates.configure_handlers(application)
        await application.initialize()
        bot = application.bot
        logger.info(f'Bot: {bot.username}')
        await set_commands()
    return application


async def set_commands():
    logger.info('Setting bot commands')
    commands = [
        BotCommand('start', 'Comenzar a recibir las lecciones'),
        BotCommand('modo', 'Configurar el modo de las lecciones (calendario o propia)'),
        BotCommand('idioma', 'Configurar el idioma de las lecciones'),
        BotCommand('stop', 'Dejar de recibir las lecciones'),
    ]
    await bot.set_my_commands(commands)


async def set_send_lesson(chat, do_send, send_msg=True):
    if chat.send_lesson == do_send: return
    chat.send_lesson = do_send
    await chat.asave()
    if send_msg:
        if chat.send_lesson:
            msg = '¡Hola! Soy el bot de lecciones de *Un Curso de Milagros*.\n\nEnvía /start para empezar'
        else:
            msg = 'Ya no enviaré las lecciones.\n\nPara volver a recibirlas, manda el mensaje */start*'
        await bot.send_message(chat.chat_id, msg, parse_mode=ParseMode.MARKDOWN)


def send_today_shortly(chat):
    async def task():
        await asyncio.sleep(3)
        await do_send_today(chat)
    asyncio.create_task(task())


async def get_chat(chat_id):
    chat = await Chat.objects.filter(chat_id=chat_id).afirst()
    if not chat:
        chat = Chat(chat_id=chat_id)
        await chat.asave()
    return chat


async def set_lesson_mode(chat_id, is_calendar, lesson_number=None):
    assert is_calendar or lesson_number is not None
    chat = await get_chat(chat_id)
    if is_calendar:
        if chat.is_calendar: return
        chat.is_calendar = True
        chat.last_lesson_sent = None
    else:
        chat.is_calendar = False
        chat.last_lesson_sent = lesson_number - 1
    chat.last_sent = None
    await chat.asave()
    send_today_shortly(chat)


async def set_language(chat_id, language):
    assert language is not None
    chat = await get_chat(chat_id)
    if chat.language != language:
        chat.language = language
        chat.last_sent = None
        await chat.asave()
        send_today_shortly(chat)


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
        return
    if now.hour < 8 or now.hour >= 23:
        return
    await do_send_today(chat)


async def do_send_today(chat):
    if chat.is_calendar:
        lesson_number = get_day_lesson_number(datetime.now().date())
    else:
        lesson_number = chat.last_lesson_sent if chat.last_lesson_sent else -1
        lesson_number += 1
        if lesson_number < 0 or lesson_number > 364:
            lesson_number = 0
    await send_lesson(chat, lesson_number, language=chat.language)


def can_send_today(today, chat):
    if not chat.last_sent:
        return True
    return (today - chat.last_sent).days >= 1


async def send_lesson(chat, lesson_number, language=None):
    logger.info(f'Sending lesson {lesson_number + 1} to {chat}')
    for text in get_day_texts(lesson_number, language=language):
        await __send_lesson_text(chat.chat_id, text)
    chat.last_sent = datetime.now().date()
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
