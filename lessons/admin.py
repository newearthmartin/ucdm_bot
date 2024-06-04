from marto_python.admin import register_admin
from .models import Chat
from django.contrib.admin import ModelAdmin
# from asgiref.sync import async_to_sync
# from . import bot_updates


class ChatAdmin(ModelAdmin):
    list_display = ['pk', 'chat_id', 'username', 'is_group', 'send_lesson']
    # actions = ['retrieve_name']
    #
    # def retrieve_name(self, request, queryset):
    #     async_to_sync(bot_updates.initialize_bot)()  # TODO: find better way to do this, so we don't have to initialize in every action
    #     for chat in queryset.all():
    #         async_to_sync(bot_updates.retrieve_chat_name)(chat)


register_admin(Chat, ChatAdmin)
