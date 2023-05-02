import logging
from django.conf import settings
from django.urls import reverse
from telegram import Bot, Update, BotCommand
from telegram.constants import ChatType, ChatMemberStatus, ParseMode
from datetime import datetime
from .workbook import get_day_texts, get_day_lesson_number
from .models import Chat
from . import views

logger = logging.getLogger(__name__)

bot = None


async def initialize_bot(with_webhooks):
    global bot
    if not bot:
        bot = Bot(token=settings.TELEGRAM_TOKEN)
        if with_webhooks:
            logger.info('Initializing bot with webhooks')
            webhooks_url = settings.TELEGRAM_WEBHOOKS_SERVER + reverse(views.webhooks_view)
            await bot.set_webhook(webhooks_url, secret_token=settings.TELEGRAM_SECRET_TOKEN)
        else:
            logger.info('Initializing bot without webhooks')
            await bot.delete_webhook()
        await set_commands(bot)
    return bot


async def set_commands(bot):
    commands = [
        BotCommand('start', 'Comenzar a recibir las lecciones'),
        BotCommand('modo', 'Configurar el modo de las lecciones (calendario o propia)'),
        BotCommand('stop', 'Dejar de recibir las lecciones'),
    ]
    await bot.set_my_commands(commands)


async def process_update(update):
    if update.my_chat_member:
        await process_chat_member(update, None)
    elif update.message:
        await process_message(update)


async def process_chat_member(update, context):
    logger.info('Processing chat member update')
    my_chat_member = update.my_chat_member
    new_chat_member = my_chat_member and update.my_chat_member.new_chat_member
    chat = my_chat_member and my_chat_member.chat
    if new_chat_member and new_chat_member.user.id == bot.id:
        if new_chat_member.status == ChatMemberStatus.MEMBER:
            await set_chat_status(bot, chat.id, True, is_group=True, send_msg=True)
        elif new_chat_member.status == ChatMemberStatus.LEFT:
            await set_chat_status(bot, chat.id, False, send_msg=False)


async def process_message(update):
    message = update.message
    chat = message.chat
    if not chat:
        logger.error(f'Chat expected: {update}')
        return
    if chat.type == ChatType.PRIVATE:
        is_group = False
    elif chat.type == ChatType.GROUP:
        is_group = True
    else:
        logging.error(f'Unexpected chat type {chat.type}')
        return
    if message.text == '/start':
        await set_chat_status(bot, chat.id, True, is_group=is_group, send_msg=True)
    elif message.text == '/stop':
        await set_chat_status(bot, chat.id, False, send_msg=True)
    else:
        logger.error(f'Unexpected message in {chat.id}: {message.text}')


async def set_chat_status(bot, chat_id, send_lesson, is_group=False, send_msg=True):
    modified = await __modify_chat_status(chat_id, is_group, send_lesson)
    if modified and send_msg:
        if send_lesson:
            msg = "Hola!\n\nA partir de ahora voy a estar mandando las lecciones todos los días.\n\nPara frenar las lecciones manda el mensaje */stop*"
        else:
            msg = "Ya no enviaré las lecciones.\n\nPara volver a recibirlas, manda el mensaje */start*"
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


async def try_send_all(bot):
    chats = Chat.objects.filter(send_lesson=True)
    chat_count = await chats.acount()
    logger.info(f'Sending to {chat_count} chats')
    async for chat in Chat.objects.filter(send_lesson=True).all():
        await try_send_today(bot, chat)


__DATE_FORMAT = '%Y-%m-%d'


async def try_send_today(bot, chat):
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
    await send_lesson(bot, chat, today, lesson_number)


def can_send_today(today, chat):
    if not chat.last_sent:
        return True
    return (today - chat.last_sent).days >= 1


async def send_lesson(bot, chat, today, lesson_number):
    logger.info(f'Sending day {lesson_number} to {chat}')
    for text in get_day_texts(lesson_number):
        await __send_lesson_text(bot, chat.chat_id, text)
    chat.last_sent = today
    chat.last_lesson_sent = lesson_number
    await chat.asave()


async def __send_lesson_text(bot, chat_id, text):
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
