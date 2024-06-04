from marto_python.admin import register_admin
from .models import Chat
from django.contrib.admin import ModelAdmin


class ChatAdmin(ModelAdmin):
    list_display = ['pk', 'chat_id', 'username', 'is_group', 'send_lesson']


register_admin(Chat, ChatAdmin)
