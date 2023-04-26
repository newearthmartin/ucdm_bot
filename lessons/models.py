from django.db import models


class Chat(models.Model):
    chat_id = models.IntegerField(unique=True)
    is_group = models.BooleanField(default=False)
    send_lesson = models.BooleanField(default=False)
    last_sent = models.DateField(null=True, blank=True)
    last_lesson_sent = models.IntegerField(blank=True, null=True)