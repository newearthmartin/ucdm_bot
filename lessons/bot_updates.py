import logging
from enum import Enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ChatMemberStatus, ParseMode, ChatType
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, ChatMemberHandler, \
    MessageHandler, filters
from . import bot as bot_module


logger = logging.getLogger(__name__)


class State(Enum): LESSON_TYPES, LESSON_NUMBER, LESSON_LANGUAGE = range(3)
class LessonType(Enum): CALENDAR = 'Calendario'; OWN = 'Propia'
class LessonLanguage(Enum): ES = 'Castellano'; EN = 'English'


def configure_handlers(application: Application):
    start_handler = ConversationHandler(entry_points=[CommandHandler('start', start_state)], states={}, fallbacks=[])
    mode_handler = ConversationHandler(
        entry_points=[CommandHandler('modo', lesson_mode_state)],
        states={
            State.LESSON_TYPES: [
                MessageHandler(filters.Regex(f'^({LessonType.CALENDAR.value}|{LessonType.OWN.value})$'), lesson_types_state)],
            State.LESSON_NUMBER: [MessageHandler(filters.TEXT, lesson_number_state)],
        }, fallbacks=[CommandHandler('cancel', cancel_state)]
    )
    language_handler = ConversationHandler(
        entry_points=[CommandHandler('idioma', language_state)],
        states={
            State.LESSON_LANGUAGE: [
                MessageHandler(filters.Regex(f'^({LessonLanguage.ES.value}|{LessonLanguage.EN.value})$'), language_set_state)],
        }, fallbacks=[CommandHandler('cancel', cancel_state)]
    )
    stop_handler = ConversationHandler(entry_points=[CommandHandler('stop', stop_state)], states={}, fallbacks=[])
    member_handler = ChatMemberHandler(process_chat_member)
    application.add_handler(start_handler)
    application.add_handler(mode_handler)
    application.add_handler(language_handler)
    application.add_handler(stop_handler)
    application.add_handler(member_handler)


async def start_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - start_state')
    await update.message.reply_text(
        '¡Hola! A partir de hoy te enviaré las lecciones de *Un Curso de Milagros* todos los días.\n\n'
        'Envía /modo para seleccionar el modo de lecciones (calendario o propia)\n'
        'Envía /stop para dejar de recibir las lecciones.\n', parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    await bot_module.set_send_lesson(chat, True, send_msg=False)
    return ConversationHandler.END


async def stop_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - stop_state')
    await bot_module.set_send_lesson(chat, False, send_msg=False)
    await update.message.reply_text(
        'Ya no recibirás más las lecciones.\n\n'
        'Envía /start para volver a recibirlas.\n', parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def language_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [[LessonLanguage.ES.value, LessonLanguage.EN.value]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                       input_field_placeholder='¿Lenguaje?')
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - language_state')
    language = LessonLanguage[chat.language.upper()]
    await update.message.reply_text(
        '¿En qué lenguaje quieres las lecciones?\n\n'
        f'Actualmente estás recibiendo las lecciones en: {language.value}\n\n'
        'Envía /cancel para abandonar esta opción.\n',
        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return State.LESSON_LANGUAGE


async def language_set_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    language = LessonLanguage(update.message.text)
    logger.info(f'{chat} - {update.message.from_user.username} - language_set_state - {language}')
    await update.message.reply_text(
        f'Recibirás la lección del día en: {language.value}',
        reply_markup=ReplyKeyboardRemove())
    await bot_module.set_language(get_chat_id(update), language.name.lower())
    return ConversationHandler.END


async def lesson_mode_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - lesson_mode_state')

    reply_keyboard = [[LessonType.CALENDAR.value, LessonType.OWN.value]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                       input_field_placeholder='¿Tipo de lección?')
    await update.message.reply_text(
        '¿Quieres la lección del día según el calendario o ir en tu propia lección?\n\n'
        'Envía /cancel para abandonar esta opción.\n',
        parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return State.LESSON_TYPES


async def lesson_types_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    lesson_type = LessonType(update.message.text)
    logger.info(f'{chat} - {update.message.from_user.username} - lesson_types_state - {lesson_type}')
    if lesson_type == LessonType.CALENDAR:
        await update.message.reply_text(
            'Recibirás la lección del día según el calendario.',
            reply_markup=ReplyKeyboardRemove())
        await bot_module.set_lesson_mode(get_chat_id(update), True)
        return ConversationHandler.END
    elif lesson_type == LessonType.OWN:
        await update.message.reply_text(
            'Ingresa el número de lección (1 - 365) que quieres recibir hoy:\n',
            reply_markup=ReplyKeyboardRemove())
        return State.LESSON_NUMBER


async def lesson_number_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def cancel_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat = await get_or_create_chat(update)
    logger.info(f'{chat} - {update.message.from_user.username} - cancel_state')
    await update.message.reply_text('Opción cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_chat_id(update: Update) -> int:
    if update.message and update.message.chat:
        return update.message.chat_id
    elif update.my_chat_member and update.my_chat_member.chat:
        return update.my_chat_member.chat.id
    else:
        return None


async def get_or_create_chat(update: Update):
    chat_id = get_chat_id(update)
    chat = await bot_module.get_chat(chat_id)
    message_chat = (update.message and update.message.chat) or (update.my_chat_member and update.my_chat_member.chat)
    if message_chat and message_chat.type == ChatType.GROUP:
        if not chat.is_group:
            chat.is_group = True
            await chat.asave()
            logger.info(f'{chat} - set as group')
    return chat


async def process_chat_member(update, context: ContextTypes.DEFAULT_TYPE):
    my_chat_member = update.my_chat_member
    new_chat_member = my_chat_member and update.my_chat_member.new_chat_member

    if new_chat_member and new_chat_member.user.id == bot_module.bot.id:
        chat = await get_or_create_chat(update)
        logger.info(f'{chat} - process_chat_member - {new_chat_member.status}')
        if new_chat_member.status == ChatMemberStatus.MEMBER:
            await bot_module.set_send_lesson(chat, True, send_msg=True)
            await bot_module.send_today_shortly(chat)
        elif new_chat_member.status == ChatMemberStatus.LEFT:
            await bot_module.set_send_lesson(chat, False, send_msg=False)
