#!/usr/bin/env -S PYENV_VERSION=ucdm DJANGO_SETTINGS_MODULE=ucdm_bot.settings python
# pylint: disable=unused-argument, wrong-import-position

import django
django.setup()

import logging
from django.conf import settings
from enum import Enum
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
    LESSON_TYPES, LESSON_NUMBER = range(2)


class LessonType(Enum):
    CALENDAR = 'Calendario'
    OWN = 'Propia'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = '¡Hola! A partir de hoy te enviaré las lecciones de *Un Curso de Milagros* todos los días.\n\n' \
          'Envía /modo para seleccionar el modo de lecciones (calendario o propia)\n' \
          'Envía /stop para dejar de recibir las lecciones.\n',
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = 'Ya no recibirás más las lecciones.\n\n' \
          'Envía /start para volver a recibirlas.\n'
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def lesson_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = '¿Quieres la lección del día según el calendario o ir en tu propia lección?\n\n' \
          'Envía /cancel para abandonar esta opción.\n' \
          'Envía /stop para dejar de recibir las lecciones.\n'
    reply_keyboard = [[LessonType.CALENDAR.value, LessonType.OWN.value]]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                       input_field_placeholder='¿Tipo de lección?')
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    return State.LESSON_TYPES


async def lesson_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lesson_type = LessonType(update.message.text)
    logger.info(f'Lesson type chosen: {lesson_type}')
    if lesson_type == LessonType.CALENDAR:
        msg = 'Recibirás la lección del día según el calendario.'
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    elif lesson_type == LessonType.OWN:
        msg = 'Ingresa el número de lección que quieres recibir hoy:\n(1 para la primera lección)'
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        return State.LESSON_NUMBER


async def lesson_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        number = int(update.message.text)
    except ValueError:
        number = None
    if number is None or number < 1 or number > 365:
        msg = 'No es un número válido. Por favor ingresa un número entre 1 y 365:'
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        return State.LESSON_NUMBER
    logger.info(f'Lesson number selected {number}')
    msg = f'Recibirás las lecciones empezando hoy por la número {number}.'
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f'User {user.first_name} canceled the conversation.')
    await update.message.reply_text('Opción cancelada.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


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
