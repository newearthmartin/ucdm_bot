#!/bin/bash
export PYENV_VERSION=ucdm
export DJANGO_SETTINGS_MODULE=ucdm_bot.settings
./manage.py runserver 0.0.0.0:8000
