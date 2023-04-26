import logging
from telegram.constants import ChatType, ChatMemberStatus, ParseMode
from datetime import datetime
from .workbook import get_day_texts, get_day_lesson_number
from .models import Chat

logger = logging.getLogger(__name__)


async def get_updates(bot):
    updates = await bot.get_updates()
    chats_added = {}
    chats_removed = set()

    for update in updates:
        message = update.message
        my_chat_member = update.my_chat_member
        new_chat_member = my_chat_member and my_chat_member.new_chat_member
        if new_chat_member and new_chat_member.user.id == bot.id:
            chat = my_chat_member and my_chat_member.chat
            if new_chat_member.status == ChatMemberStatus.MEMBER:
                chats_added[chat.id] = True
                chats_removed.discard(chat.id)
            elif new_chat_member.status == ChatMemberStatus.LEFT:
                chats_added.pop(chat.id, None)
                chats_removed.add(chat.id)
        if message:
            chat = message.chat
            if not chat: continue
            if chat.type == ChatType.PRIVATE:
                is_group = False
            elif chat.type == ChatType.GROUP:
                is_group = True
            else:
                logging.error(f'unexpected chat type {chat.type}')
                continue
            if message.text == '/start':
                chats_added[chat.id] = is_group
                chats_removed.discard(chat.id)
            elif message.text == '/stop':
                chats_added.pop(chat.id, None)
                chats_removed.add(chat.id)
            else:
                logger.error(f'unexpected message in {chat.id}: {message.text}')
                continue

    for chat_id, is_group in chats_added.items(): await set_chat_status(bot, chat_id, is_group, True)
    for chat_id in chats_removed: await set_chat_status(bot, chat_id, None, False)


async def set_chat_status(bot, chat_id, is_group, send_lesson):
    modified = await __modify_chat_status(chat_id, is_group, send_lesson)
    if modified:
        if send_lesson:
            await bot.send_message(
                chat_id,
                "Hola!\n\nA partir de ahora voy a estar mandando las lecciones todos los días.\n\nPara frenar las lecciones manda el mensaje */stop*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await bot.send_message(
                chat_id,
                "Ya no enviaré las lecciones.\n\nPara volver a recibirlas, manda el mensaje */start*",
                parse_mode = ParseMode.MARKDOWN
            )


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
