from workbook import get_day_texts, get_day_lesson_number
from telegram.constants import ChatType, ChatMemberStatus, ParseMode
from datetime import datetime
from db import db_get, db_set

DATE_FORMAT = '%Y-%m-%d'


async def try_send_all(bot):
    groups = get_joined_groups()
    if not groups:
        print('No groups to send to')
        return
    print(f'Sending to {len(groups)} groups')
    for group_id in groups:
        await try_send_today(bot, group_id)


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
    db_set(f'{chat_id}.last_sent', today.strftime(DATE_FORMAT))


def can_send_today(today, chat_id):
    last_sent = db_get(f'{chat_id}.last_sent')
    if not last_sent:
        return True
    last_sent = datetime.strptime(last_sent, DATE_FORMAT).date()
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


async def get_updates(bot):
    updates = await bot.get_updates()
    groups_added = set()
    groups_removed = set()
    for update in updates:
        my_chat_member = update.my_chat_member
        new_chat_member = my_chat_member and my_chat_member.new_chat_member
        chat = my_chat_member and my_chat_member.chat
        if new_chat_member and new_chat_member.user.id == bot.id:
            if new_chat_member.status == ChatMemberStatus.MEMBER:
                if chat.type == ChatType.GROUP:
                    groups_added.add(chat.id)
                    groups_removed.discard(chat.id)
            elif new_chat_member.status == ChatMemberStatus.LEFT:
                if chat.type == ChatType.GROUP:
                    groups_removed.add(chat.id)
                    groups_added.discard(chat.id)
    for group_id in groups_added:
        modified = group_status(group_id, True)
        if modified:
            await try_send_today(bot, group_id)
    for group_id in groups_removed:
        group_status(group_id, False)


def get_joined_groups():
    return db_get('groups', [])


def group_status(group_id, join_not_left):
    modified = False
    groups = get_joined_groups()
    if join_not_left and group_id not in groups:
        groups.append(group_id)
        modified = True
    if not join_not_left and group_id in groups:
        groups.remove(group_id)
        modified = True
    if modified:
        db_set('groups', groups)
        action = 'JOINED' if join_not_left else 'LEFT'
        print(f'Set group {group_id} as {action}')
    return modified
