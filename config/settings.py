# config/settings.py - ДОБАВЛЯЕМ vehicles
import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-render')

# Убираем кастомную модель пользователя
# AUTH_USER_MODEL = 'users.User'  # КОММЕНТИРУЕМ

# Добавляем проверки для отключения
SILENCED_SYSTEM_CHECKS = [
    'fields.E304',
    'models.W042',
    'auth.E003',  # Отключаем проверку groups
    'auth.E004',  # Отключаем проверку user_permissions
]

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django REST Framework (нужен для API)
    'rest_framework',

    # Только рабочие приложения
    'users',      # приложение с авторизацией
    'dashboard',  # панель управления
    'vehicles',   # мониторинг транспорта ← ДОБАВЛЯЕМ

    # ВРЕМЕННО комментируем остальные
    # 'billing',
    # 'support',
    # 'api',
    # 'reports',

    # ВРЕМЕННО комментируем сторонние
    # 'corsheaders',
    # 'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Убираем валидаторы паролей
AUTH_PASSWORD_VALIDATORS = []

# Настройки аутентификации
AUTHENTICATION_BACKENDS = [
    'users.backend.AutoGraphAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Отключаем security настройки для разработки
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Настройки сессии
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_NAME = 'autograph_sessionid'

# Логирование - ДОБАВЛЯЕМ vehicles
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'users': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'vehicles': {  # ← ДОБАВЛЯЕМ
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Создаем директории если нет
os.makedirs(STATIC_ROOT, exist_ok=True)

# AutoGRAPH API настройки
AUTOGRAPH_API_BASE_URL = os.getenv('AUTOGRAPH_API_BASE_URL', "https://web.tk-ekat.ru")
AUTOGRAPH_API_TIMEOUT = int(os.getenv('AUTOGRAPH_API_TIMEOUT', 30))

# Настройки аутентификации
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_URL = '/auth/logout/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Django REST Framework настройки (включаем)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# CORS настройки (для разработки)
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# Настройки кэша
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Настройки для vehicles app (дополнительные)
VEHICLES_CACHE_TIMEOUT = 300  # 5 минут кэш для данных ТС