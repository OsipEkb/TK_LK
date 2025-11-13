import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-render')

SILENCED_SYSTEM_CHECKS = ['fields.E304', 'models.W042']

# Оставляем кастомную модель пользователя
AUTH_USER_MODEL = 'users.User'
# ВРЕМЕННО: всегда DEBUG для диагностики
DEBUG = True

# ВРЕМЕННО: разрешаем все хосты
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',      # ПЕРВЫМ
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ПОТОМ кастомные приложения
    'users',                    # приложение с User моделью
    'vehicles',
    'dashboard',
    'billing',
    'support',
    'api',

    # Сторонние
    'rest_framework',
    'corsheaders',
    'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Важно для статики
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
        'DIRS': [BASE_DIR / 'templates'],  # ДОБАВЬ ЭТУ СТРОКУ!
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

# База данных - SQLite (проще для начала)
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

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise для статических файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ВРЕМЕННО отключаем все security настройки
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Логирование для диагностики
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Создаем директории если нет
os.makedirs(STATIC_ROOT, exist_ok=True)

# AutoGRAPH API настройки
AUTOGRAPH_API_BASE_URL = os.getenv('AUTOGRAPH_API_BASE_URL', 'https://web.tk-ekat.ru')
AUTOGRAPH_API_TIMEOUT = int(os.getenv('AUTOGRAPH_API_TIMEOUT', 30))

# Настройки аутентификации
LOGIN_URL = '/auth/login/'  # URL для входа
LOGIN_REDIRECT_URL = '/dashboard/'  # Куда редиректить после успешного входа
LOGOUT_REDIRECT_URL = '/auth/login/'  # Куда редиректить после выхода