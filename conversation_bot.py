#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position

from enum import Enum
import logging
import django
django.setup()
from django.conf import settings
from telegram.constants import ParseMode
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    ChatMemberHandler,
    MessageHandler,
    filters,
)
from lessons import bot as bot_module
from lessons.bot import process_chat_member

logger = logging.getLogger(__name__)


class State(Enum):
    GENDER, PHOTO, LOCATION, BIO, LESSON_TYPES, LESSON_NUMBER = range(6)


class LessonType(Enum):
    CALENDAR = 'Calendario'
    OWN = 'Propia'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        '¡Hola! A partir de hoy te enviaré las lecciones de *Un Curso de Milagros* todos los días.\n\n'
        'Envía /modo para seleccionar el modo de lecciones (calendario o propia)\n'
        'Envía /stop para dejar de recibir las lecciones.\n',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Ya no recibirás más las lecciones.\n\n'
        'Envía /start para volver a recibirlas.\n',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def lesson_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [[LessonType.CALENDAR.value, LessonType.OWN.value]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder='¿Tipo de lección?')
    await update.message.reply_text(
        '¿Quieres la lección del día según el calendario o ir en tu propia lección?\n\n'
        'Envía /cancel para abandonar esta opción.\n'
        'Envía /stop para dejar de recibir las lecciones.\n',
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    return State.LESSON_TYPES


async def lesson_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lesson_type = LessonType(update.message.text)
    logger.info(f'Lesson type chosen: {lesson_type}')
    if lesson_type == LessonType.CALENDAR:
        await update.message.reply_text('Recibirás la lección del día según el calendario.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif lesson_type == LessonType.OWN:
        await update.message.reply_text(
            'Ingresa el número de lección que quieres recibir hoy:\n(1 para la primera lección)',
            reply_markup=ReplyKeyboardRemove()
        )
        return State.LESSON_NUMBER


async def lesson_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        number = int(update.message.text)
    except ValueError:
        number = None
    if number is None or number < 1 or number > 365:
        await update.message.reply_text(
            'No es un número válido. Por favor ingresa un número entre 1 y 365:',
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.LESSON_NUMBER
    logger.info(f'Lesson number selected {number}')
    await update.message.reply_text(
        f'Recibirás las lecciones empezando hoy por la número {number}.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f'User {user.first_name} canceled the conversation.')
    await update.message.reply_text('Opción cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)


def main():
    application = Application.builder().token(settings.TELEGRAM_TOKEN).build()
    bot_module.bot = application.bot
    start_handler = ConversationHandler(entry_points=[CommandHandler('start', start)], states={}, fallbacks=[])
    mode_handler = ConversationHandler(
        entry_points=[CommandHandler('modo', lesson_mode)],
        states={
            State.LESSON_TYPES: [MessageHandler(filters.Regex(f'^({LessonType.CALENDAR.value}|{LessonType.OWN.value})$'), lesson_types)],
            State.LESSON_NUMBER: [MessageHandler(filters.TEXT, lesson_number)],
        }, fallbacks=[CommandHandler('cancel', cancel)]
    )
    stop_handler = ConversationHandler(entry_points=[CommandHandler('stop', stop)], states={}, fallbacks=[])
    member_handler = ChatMemberHandler(process_chat_member)

    application.add_handler(start_handler)
    application.add_handler(mode_handler)
    application.add_handler(stop_handler)
    application.add_handler(member_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
