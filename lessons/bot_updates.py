import logging
from telegram import Update
from telegram.constants import ChatType, ChatMemberStatus
from .bot import bot, set_chat_status

logger = logging.getLogger(__name__)


def get_chat_id(update: Update) -> int:
    if update.message and update.message.chat:
        return update.message.chat_id
    elif update.my_chat_member and update.my_chat_member.chat:
        return update.my_chat_member.chat
    else:
        return None


async def process_update(update):
    if update.my_chat_member:
        await process_chat_member(update, None)
    elif update.message:
        await process_message(update)


async def process_chat_member(update, context):
    logger.info('Processing chat member update')
    my_chat_member = update.my_chat_member
    new_chat_member = my_chat_member and update.my_chat_member.new_chat_member
    chat_id = get_chat_id(update)
    if new_chat_member and new_chat_member.user.id == bot.id:
        if new_chat_member.status == ChatMemberStatus.MEMBER:
            await set_chat_status(chat_id, True, is_group=True, send_msg=True)
        elif new_chat_member.status == ChatMemberStatus.LEFT:
            await set_chat_status(chat_id, False, send_msg=False)


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
        await set_chat_status(chat.id, True, is_group=is_group, send_msg=True)
    elif message.text == '/stop':
        await set_chat_status(chat.id, False, send_msg=True)
    else:
        logger.error(f'Unexpected message in {chat.id}: {message.text}')


