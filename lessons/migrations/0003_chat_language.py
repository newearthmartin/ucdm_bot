# Generated by Django 4.2 on 2023-05-05 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0002_chat_is_calendar'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='language',
            field=models.CharField(default='es', max_length=8),
        ),
    ]
