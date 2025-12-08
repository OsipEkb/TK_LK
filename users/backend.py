# users/backend.py
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
import logging
import requests

logger = logging.getLogger(__name__)

# Импортируем клиент API
try:
    from .api_client import AutoGraphAPIClient
except ImportError:
    # Создаем упрощенную версию если файл не найден
    class AutoGraphAPIClient:
        BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

        def __init__(self):
            self.session = requests.Session()

        def login(self, username, password, utc_offset=300):
            url = f"{self.BASE_URL}/Login"
            params = {
                'UserName': username,
                'Password': password,
                'UTCOffset': utc_offset
            }

            try:
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200 and response.text.strip():
                    return response.text.strip()
            except Exception:
                pass
            return None


class AutoGraphAuthBackend(BaseBackend):
    """Бэкенд аутентификации через AutoGRAPH API"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Аутентификация через AutoGRAPH API"""
        if not username or not password:
            logger.warning("No username or password provided")
            return None

        try:
            logger.info(f"🔐 AutoGRAPH authentication attempt: {username}")

            # ОЧИЩАЕМ СТАРЫЕ ДАННЫЕ ПЕРЕД НОВОЙ АУТЕНТИФИКАЦИЕЙ
            if request and hasattr(request, 'session'):
                self._clear_session_cache(request.session)

            # Прямой вызов API AutoGRAPH
            api_url = f"{settings.AUTOGRAPH_API_BASE_URL}/ServiceJSON/Login"
            params = {
                'UserName': username,
                'Password': password,
                'UTCOffset': 180  # Moscow UTC+3
            }

            response = requests.get(api_url, params=params, timeout=30)

            if response.status_code == 200 and response.text.strip():
                token = response.text.strip()
                logger.info(f"✅ AutoGRAPH auth successful for {username}")

                # Сохраняем токен в сессии
                request.session['autograph_token'] = token
                request.session['autograph_username'] = username
                request.session['autograph_authenticated'] = True
                request.session.set_expiry(86400)  # 24 часа

                # Возвращаем объект пользователя
                user = SimpleUser(username)
                user.autograph_token = token  # Добавляем токен в объект

                return user
            else:
                logger.error(f"❌ AutoGRAPH auth failed for {username}: Status {response.status_code}")
                if response.status_code == 401:
                    logger.error("Invalid credentials")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"🔌 Connection error during auth: {e}")
            return None
        except Exception as e:
            logger.error(f"💥 Authentication error for {username}: {e}")
            return None

    def _clear_session_cache(self, session):
        """Очистка кэша сессии"""
        # Удаляем все ключи, связанные с AutoGRAPH данными
        keys_to_remove = [key for key in session.keys() if key.startswith('autograph_')]

        for key in keys_to_remove:
            del session[key]

        logger.info("🧹 Cleared AutoGRAPH session cache")


class SimpleUser:
    """Упрощенный объект пользователя для Django"""

    def __init__(self, username):
        self.username = username
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.pk = self._generate_user_id(username)

        # Для совместимости с Django
        self._auth_user_hash = hash(f"{username}_{id(self)}")
        self.backend = 'users.backend.AutoGraphAuthBackend'

    def __str__(self):
        return self.username

    def get_username(self):
        return self.username

    def _generate_user_id(self, username):
        """Генерация уникального ID для пользователя"""
        import hashlib
        return int(hashlib.md5(username.encode()).hexdigest()[:8], 16)

    @property
    def id(self):
        return self.pk

    # Методы для совместимости
    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username