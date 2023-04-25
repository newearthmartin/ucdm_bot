from workbook import get_day_texts, get_day_lesson_number
from telegram.constants import ChatType, ChatMemberStatus, ParseMode
from datetime import datetime
from db import db_get, db_set


async def get_updates(bot):
    updates = await bot.get_updates()
    groups_added = set()
    groups_removed = set()
    private_chats_added = set()
    private_chats_removed = set()

    for update in updates:
        message = update.message
        my_chat_member = update.my_chat_member
        new_chat_member = my_chat_member and my_chat_member.new_chat_member
        if new_chat_member and new_chat_member.user.id == bot.id:
            chat = my_chat_member and my_chat_member.chat
            if new_chat_member.status == ChatMemberStatus.MEMBER:
                if chat.type == ChatType.GROUP:
                    groups_added.add(chat.id)
                    groups_removed.discard(chat.id)
            elif new_chat_member.status == ChatMemberStatus.LEFT:
                if chat.type == ChatType.GROUP:
                    groups_removed.add(chat.id)
                    groups_added.discard(chat.id)
        if message:
            chat = message.chat
            if not chat: continue
            if chat.type == ChatType.PRIVATE:
                added, removed = private_chats_added, private_chats_removed
            elif chat.type == ChatType.GROUP:
                added, removed = groups_added, groups_removed
            else:
                continue
            if message.text == '/start':
                added.add(chat.id)
                removed.discard(chat.id)
            elif message.text == '/stop':
                added.discard(chat.id)
                removed.add(chat.id)
            else:
                print(f'unexpected message in {chat.id}: {message.text}')
                continue
    await update_chats_status(bot, 'groups', groups_added, groups_removed)
    await update_chats_status(bot, 'private_chats', private_chats_added, private_chats_removed)


async def update_chats_status(bot, db_key, chats_added, chats_removed):
    for chat_id in chats_added:
        modified = chat_status(db_key, chat_id, True)
        if modified:
            await bot.send_message(chat_id, "Hola!\n\nA partir de ahora voy a estar mandando las lecciones todos los días.\n\nPara frenar las lecciones manda el mensaje */stop*", parse_mode = ParseMode.MARKDOWN)
            await try_send_today(bot, chat_id)
    for chat_id in chats_removed:
        modified = chat_status(db_key, chat_id, False)
        if modified:
            await bot.send_message(chat_id, "Ya no enviaré las lecciones.\n\nPara volver a recibirlas, manda el mensaje */start*", parse_mode = ParseMode.MARKDOWN)



def chat_status(db_key, chat_id, join_not_left):
    modified = False
    chats = db_get(db_key, [])
    if join_not_left and chat_id not in chats:
        chats.append(chat_id)
        modified = True
    if not join_not_left and chat_id in chats:
        chats.remove(chat_id)
        modified = True
    if modified:
        db_set(db_key, chats)
        action = 'JOINED' if join_not_left else 'LEFT'
        print(f'Set {db_key} status {chat_id} - {action}')
    return modified


async def try_send_all(bot):
    chats = db_get('groups', []) + db_get('private_chats', [])
    if not chats:
        print('No chats')
        return
    print(f'Sending to {len(chats)} chats')
    for chat_id in chats:
        await try_send_today(bot, chat_id)


__DATE_FORMAT = '%Y-%m-%d'


async def try_send_today(bot, chat_id):
    now = datetime.now()
    today = now.date()
    if not can_send_today(today, chat_id):
        print(f'Already sent today\'s lesson to chat {chat_id}')
        return
    if now.hour < 8:
        print(f'Too early to send to chat {chat_id}')
        return
    if now.hour >= 23:
        print(f'Too late to send to chat {chat_id}')
        return
    lesson_number = get_day_lesson_number(today)
    if lesson_number is None:
        print(f'No lesson for {today}')
        return
    await send_day(bot, chat_id, lesson_number)
    db_set(f'{chat_id}.last_sent', today.strftime(__DATE_FORMAT))


def can_send_today(today, chat_id):
    last_sent = db_get(f'{chat_id}.last_sent')
    if not last_sent:
        return True
    last_sent = datetime.strptime(last_sent, __DATE_FORMAT).date()
    return (today - last_sent).days >= 1


async def send_day(bot, chat_id, day):
    print(f'Sending day {day} to chat {chat_id}')
    for text in get_day_texts(day):
        await send_lesson_text(bot, chat_id, text)


async def send_lesson_text(bot, chat_id, text):
    messages = split_for_telegram(text)
    if len(messages) > 1:
        part_lengths = [len(message) for message in messages]
        print(f'Splitting message of length {len(text)} into {len(messages)} parts of lengths {part_lengths}')
    else:
        print(f'Sending message of length {len(text)}')
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
