import json
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from telegram import Update
from . import bot as bot_module

logger = logging.getLogger(__name__)


@csrf_exempt
def webhooks_view(request):  # TODO: hacer async view?
    secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token', None)
    if secret_token != settings.TELEGRAM_SECRET_TOKEN: return HttpResponseForbidden()

    logger.info('received webhooks')
    data = request.body.decode('utf-8')
    data = json.loads(data)
    update = Update.de_json(data, bot_module.bot)
    async_to_sync(bot_module.process_update)(update)
    return HttpResponse()