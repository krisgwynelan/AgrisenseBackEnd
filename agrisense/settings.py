"""
Django settings for agrisense project.
"""

from pathlib import Path
from celery.schedules import crontab
from celery.schedules import schedule
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-llg*o=ytbb8^@q56#=r0@@-&=zy9n!qu34^f5_=dtnmvr9v6hs'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'rest_framework',
    'corsheaders',
    'channels',
    'django_celery_beat',
    'rest_framework_simplejwt',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # must be on top
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'agrisense.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agrisense.wsgi.application'
ASGI_APPLICATION = 'agrisense.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # ✅ use Philippine time
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'agrisenseteam@gmail.com'
EMAIL_HOST_PASSWORD = 'rtpe ktub lphk gyjd'
DEFAULT_FROM_EMAIL = 'noreply@agrisense.com'

# ✅ Channels + Redis
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# ✅ Celery configuration
from celery.schedules import crontab 


CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

CELERY_BEAT_SCHEDULE = {
    "send-daily-notification-at-midnight": {
        "task": "accounts.tasks.send_daily_summary",
        "schedule": crontab(minute=0, hour=0),  # runs every 12 AM
    },
}

##"schedule": crontab(minute="*/5"),

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
AUTH_USER_MODEL = 'accounts.CustomUser'

# ✅ Channel session middleware
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

ALLOWED_HOSTS = ["*", "192.168.1.23", "localhost"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:19006",
    "http://192.168.1.23:19006",
    "exp://192.168.1.23:19000",
]

