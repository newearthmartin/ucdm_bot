import os
from pathlib import Path
from marto_python.secrets import read_secrets, get_secret

BASE_DIR = Path(__file__).resolve().parent.parent
ADMINS = [('Martin Massera', 'martinmassera@gmail.com')]

read_secrets(base_dir=BASE_DIR)

SITE_ID = 1
DEBUG = not get_secret('PRODUCTION', default=False)
SECRET_KEY = 'django-insecure-0vt$7j1xhe7vob4i4_j&wmufbitctj&fdalr5l6y+*bslo00!^'

WORKBOOK_LANGUAGE = get_secret('WORKBOOK_LANGUAGE', 'es')

TELEGRAM_TOKEN = get_secret('TELEGRAM_TOKEN')
TELEGRAM_WEBHOOKS_SERVER = 'https://localhost.multilanguage.xyz'
TELEGRAM_SECRET_TOKEN = get_secret('TELEGRAM_SECRET_TOKEN')

DEFAULT_FROM_EMAIL = 'UCDM <ucdm@multilanguage.xyz>'
SERVER_EMAIL = 'UCDM - Server <ucdm@multilanguage.xyz>'
EMAIL_HOST = 'smtp.us.opalstack.com'
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'lessons',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ucdm_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ucdm_bot.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
    },
    'formatters': {
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'ucdm.log'),
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'root': {
        'handlers': ['console', 'file', 'mail_admins'],
        'level': 'INFO',
    },
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
