from __future__ import absolute_import, unicode_literals
from .settings import *

# changing the default user model to custom user model
AUTH_USER_MODEL = 'user_management.User'

# PostgreSQL credentials and addresses come from the shell environment. Tests
# may opt into an isolated SQLite database with DJANGO_TEST_SQLITE=true.
if os.environ.get('DJANGO_TEST_SQLITE', '').strip().lower() in ('1', 'true', 'yes', 'on'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': required_env('DB_NAME'),
            'USER': required_env('DB_USER'),
            'PASSWORD': required_env('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# To include static files to the project from static folder
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]
STATIC_ROOT = os.path.join(BASE_DIR, 'assets')


# Celery broker/result storage use Redis, configurable separately if desired.
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get(
    'CELERY_RESULT_BACKEND', CELERY_BROKER_URL
)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE', 'UTC')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_IMPORTS = (
    'user_management.tasks',
)


# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(
            os.environ.get('CHANNEL_REDIS_HOST', os.environ.get('REDIS_HOST', '127.0.0.1')),
            int(os.environ.get('CHANNEL_REDIS_PORT', os.environ.get('REDIS_PORT', '6379'))),
        )]},
    },
}

ASGI_APPLICATION = "TicketProject.routing.application"
