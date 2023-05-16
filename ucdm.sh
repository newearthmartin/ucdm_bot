#!/bin/bash
export PYENV_VERSION=ucdm
export DJANGO_SETTINGS_MODULE=ucdm_bot.settings
./manage.py runserver_plus
