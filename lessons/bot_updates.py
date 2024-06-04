import logging
from enum import Enum
from django.conf import settings
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ChatMemberStatus, ParseMode, ChatType
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, ChatMemberHandler, \
    MessageHandler, filters
from telegram.error import BadRequest
from . import bot as bot_module


logger = logging.getLogger(__name__)


class State(Enum):
    LESSON_MODE, LESSON_NUMBER, LESSON_LANGUAGE = range(1, 4)


class LessonType(Enum):
    FIRST = 'Primera'
    CALENDAR = 'Calendario'
    OTHER = 'Otra'


class LessonLanguage(Enum):
    ES = 'Castellano'
    EN = 'English'


async def initialize_bot():
    if not bot_module.bot:
        logger.info('Initializing bot')
        bot_module.application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
        configure_handlers(bot_module.application)
        await bot_module.application.initialize()
        bot_module.bot = bot_module.application.bot
        logger.info(f'Bot: {bot_module.bot.username}')
        await bot_module.set_commands()
    return bot_module.application


def enum_regex(enum_type):
    regex = '|'.join([e.value for e in enum_type])
    return f'^({regex})$'


def configure_handlers(application: Application):
    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_state), CommandHandler('modo', lesson_mode_state)],
        states={
            State.LESSON_MODE: [MessageHandler(filters.Regex(enum_regex(LessonType)), lesson_set_mode_state)],
            State.LESSON_NUMBER: [MessageHandler(filters.TEXT, lesson_number_state)]},
        fallbacks=[CommandHandler('cancel', cancel_state)], conversation_timeout=10 * 60, allow_reentry=True
    )
    language_handler = ConversationHandler(
        entry_points=[CommandHandler('idioma', language_state)],
        states={
            State.LESSON_LANGUAGE: [MessageHandler(filters.Regex(enum_regex(LessonLanguage)), language_set_state)]},
        fallbacks=[CommandHandler('cancel', cancel_state)], conversation_timeout=10 * 60, allow_reentry=True
    )
    stop_handler = ConversationHandler(entry_points=[CommandHandler('stop', stop_state)], states={}, fallbacks=[])
    member_handler = ChatMemberHandler(process_chat_member)
    application.add_handler(start_handler)
    application.add_handler(language_handler)
    application.add_handler(stop_handler)
    application.add_handler(member_handler)


async def start_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - start_state')
    options = [LessonType.FIRST.value, LessonType.CALENDAR.value, LessonType.OTHER.value]
    await update.message.reply_text(
        '¡Hola! Soy el bot de *Un Curso de Milagros* y mi propósito es enviarte las lecciones todos los días.\n\n'
        '¿Deseas comenzar con la primera lección? ¿O deseas seguir la lección del día según el calendario?\n\n'
        'Envía /cancel para cancelar.\n',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_reply_markup(options, placeholder='¿Tipo de lección?')
    )
    await bot_module.set_send_lesson(chat, True, send_msg=False)
    return State.LESSON_MODE


async def stop_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - stop_state')
    await bot_module.set_send_lesson(chat, False, send_msg=False)
    await update.message.reply_text(
        'Ya no recibirás más las lecciones.\n\n'
        'Envía /start para volver a recibirlas.\n', parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_reply_markup(options, placeholder=None):
    return ReplyKeyboardMarkup([options], one_time_keyboard=True, input_field_placeholder=placeholder)


async def language_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = get_reply_markup([LessonLanguage.ES.value, LessonLanguage.EN.value], placeholder='¿Lenguaje?')
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - language_state')
    language = LessonLanguage[chat.language.upper()]
    await update.message.reply_text(
        '¿En qué lenguaje quieres las lecciones?\n\n'
        f'Actualmente estás recibiendo las lecciones en: {language.value}\n\n'
        'Envía /cancel para abandonar esta opción.\n',
        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return State.LESSON_LANGUAGE


async def language_set_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    language = LessonLanguage(update.message.text)
    logger.info(f'{chat} - {update.message.from_user.username} - language_set_state - {language}')
    await update.message.reply_text(
        f'Recibirás la lección del día en: {language.value}',
        reply_markup=ReplyKeyboardRemove())
    await bot_module.set_language(get_chat_id(update), language.name.lower())
    return ConversationHandler.END


async def lesson_mode_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - lesson_mode_state')
    await update.message.reply_text(
        '¿Quieres la lección del día según el calendario o ir en tu propia lección?\n\n'
        'Envía /cancel para abandonar esta opción.\n',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_reply_markup([LessonType.CALENDAR.value, LessonType.OTHER.value], placeholder='¿Tipo de lección?'))
    return State.LESSON_MODE


async def lesson_set_mode_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    lesson_type = LessonType(update.message.text)
    logger.info(f'{chat} - {update.message.from_user.username} - lesson_set_mode_state - {lesson_type}')
    if lesson_type == LessonType.FIRST:
        msg = '¡Comencemos con la primera lección!'
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        await bot_module.set_lesson_mode(get_chat_id(update), False, lesson_number=0)
        return ConversationHandler.END
    elif lesson_type == LessonType.CALENDAR:
        msg = 'Recibirás la lección del día según el calendario.'
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        await bot_module.set_lesson_mode(get_chat_id(update), True)
        return ConversationHandler.END
    elif lesson_type == LessonType.OTHER or lesson_type == LessonType.OWN:
        await update.message.reply_text(
            'Ingresa el número de lección (1 - 365) que quieres recibir hoy:\n',
            reply_markup=ReplyKeyboardRemove())
        return State.LESSON_NUMBER


async def lesson_number_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        number = int(update.message.text)
    except ValueError:
        number = None
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - lesson_number_state - {number}')

    if number is None or number < 1 or number > 365:
        await update.message.reply_text(
            'No es un número válido. Por favor ingresa un número entre 1 y 365:', reply_markup=ReplyKeyboardRemove())
        return State.LESSON_NUMBER
    await update.message.reply_text(
        f'Recibirás las lecciones empezando hoy por la número {number}.', reply_markup=ReplyKeyboardRemove())
    await bot_module.set_lesson_mode(get_chat_id(update), False, lesson_number=number - 1)
    return ConversationHandler.END


async def cancel_state(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - cancel_state')
    await update.message.reply_text('Opción cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_chat_id(update: Update) -> int | None:
    if update.message and update.message.chat:
        return update.message.chat_id
    elif update.my_chat_member and update.my_chat_member.chat:
        return update.my_chat_member.chat.id
    else:
        return None


async def get_or_create_chat(update: Update):
    is_group = None
    message_chat = (update.message and update.message.chat) or (update.my_chat_member and update.my_chat_member.chat)
    if message_chat and message_chat.type == ChatType.GROUP:
        is_group = True
    chat_id = get_chat_id(update)
    chat = await bot_module.get_chat(chat_id, is_group=is_group)
    if message_chat:
        await update_name_from_message(chat, message_chat)
    return chat


async def update_name_from_message(chat, message):
    name = message and (message.username or message.title)
    if name and chat.username != name:
        logger.info(f'{chat} - updating name to "{name}"')
        chat.username = name
        await chat.asave()


async def process_chat_member(update, _: ContextTypes.DEFAULT_TYPE):
    my_chat_member = update.my_chat_member
    new_chat_member = my_chat_member and update.my_chat_member.new_chat_member

    if new_chat_member and new_chat_member.user.id == bot_module.bot.id:
        chat = await get_or_create_chat(update)
        logger.info(f'{chat} - process_chat_member - {new_chat_member.status}')
        if new_chat_member.status == ChatMemberStatus.MEMBER:
            await bot_module.set_send_lesson(chat, True, send_msg=True)
        elif new_chat_member.status == ChatMemberStatus.LEFT:
            await bot_module.set_send_lesson(chat, False, send_msg=False)


async def retrieve_chat_name(chat):
    logger.info(f'{chat} - retrieving chat name')
    try:
        info = await bot_module.bot.get_chat(chat.chat_id)
    except BadRequest:
        logger.error(f'{chat} - Bad request when retrieving chat name')
        return
    username = getattr(info, 'title') or getattr(info, 'username')
    if username and username != chat.username:
        print(f'{chat} - Updating username to "{username}"')
        chat.username = username
        await chat.asave()
