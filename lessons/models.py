from django.db import models
from django.contrib.admin import ModelAdmin


class Chat(models.Model):
    chat_id = models.IntegerField(unique=True)
    is_group = models.BooleanField(default=False)
    is_calendar = models.BooleanField(default=True)
    username = models.CharField(max_length=1024, null=True, blank=True)  # username or group name
    language = models.CharField(max_length=8, default='es')
    send_lesson = models.BooleanField(default=False)
    last_sent = models.DateField(null=True, blank=True)
    last_lesson_sent = models.IntegerField(blank=True, null=True)

    def __str__(self):
        type_str = 'chat' if not self.is_group else 'group'
        username_str = f'_{self.username}' if self.username else ''
        return f'{type_str}_{self.chat_id}{username_str}'

    class Admin(ModelAdmin):
        list_display = ['pk', 'chat_id', 'username', 'is_group', 'send_lesson']
