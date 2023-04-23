from workbook import get_day_texts
from telegram.constants import ParseMode


async def send_day(bot, chat_id, day):
    print(f'Sending day {day}')
    for text in get_day_texts(day):
        await send_lesson_text(bot, chat_id, text)


async def send_lesson_text(bot, chat_id, text):
    if not text:
        print('Can not send an empty message.')
        return
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
