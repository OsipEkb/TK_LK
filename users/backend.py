# users/backend.py
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
import logging
import requests
import hashlib

logger = logging.getLogger(__name__)


class AutoGraphAuthBackend(BaseBackend):
    """Бэкенд аутентификации через AutoGRAPH API"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Аутентификация через AutoGRAPH API"""
        if not username or not password:
            logger.warning("No username or password provided")
            return None

        try:
            logger.info(f"🔐 AutoGRAPH authentication attempt: {username}")

            # Очищаем старые данные перед новой аутентификацией
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

                # Получаем доступные схемы пользователя
                schemas = self._get_user_schemas(token)
                logger.info(f"📋 Found {len(schemas) if schemas else 0} schemas for user")

                # Сохраняем токен в сессии
                request.session['autograph_token'] = token
                request.session['autograph_username'] = username
                request.session['autograph_authenticated'] = True
                request.session.set_expiry(86400)  # 24 часа

                # Сохраняем схемы если они есть
                if schemas:
                    request.session['available_schemas'] = schemas

                    # Автоматически выбираем первую схему
                    first_schema = schemas[0]
                    request.session['autograph_schema_id'] = first_schema['id']
                    request.session['autograph_schema_name'] = first_schema['name']
                    logger.info(f"📋 Auto-selected schema: {first_schema['name']} (ID: {first_schema['id']})")

                # Возвращаем объект пользователя
                user = SimpleUser(username)
                user.autograph_token = token
                user.schema_id = request.session.get('autograph_schema_id')
                user.schema_name = request.session.get('autograph_schema_name')

                logger.info(f"👤 User object created for {username}")
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

    def _get_user_schemas(self, token):
        """Получить доступные схемы пользователя"""
        try:
            api_url = f"{settings.AUTOGRAPH_API_BASE_URL}/ServiceJSON/EnumSchemas"
            params = {'session': token}

            response = requests.get(api_url, params=params, timeout=30)

            if response.status_code == 200:
                schemas_data = response.json()
                logger.debug(f"Raw schemas response: {schemas_data}")

                if isinstance(schemas_data, list):
                    schemas = []
                    for item in schemas_data:
                        schemas.append({
                            'id': item.get('ID', ''),
                            'name': item.get('Name', 'Без названия'),
                            'group': item.get('Group', ''),
                            'groupID': item.get('GroupID', '')
                        })
                    return schemas
                else:
                    logger.warning(f"Unexpected schemas format: {type(schemas_data)}")
                    return None
            else:
                logger.error(f"Error getting schemas: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting user schemas: {e}")
            return None

    def _clear_session_cache(self, session):
        """Очистка кэша сессии"""
        # Удаляем все ключи, связанные с AutoGRAPH данными
        keys_to_remove = [key for key in session.keys() if key.startswith('autograph_')]

        for key in keys_to_remove:
            del session[key]

        logger.info("🧹 Cleared AutoGRAPH session cache")

    def get_user(self, user_id):
        """Получить пользователя по ID (требуется для Django)"""
        # В нашей реализации пользователи не хранятся в БД,
        # поэтому всегда возвращаем None
        return None


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

        # Дополнительные атрибуты для AutoGRAPH
        self.autograph_token = None
        self.schema_id = None
        self.schema_name = None

    def __str__(self):
        return self.username

    def get_username(self):
        return self.username

    def _generate_user_id(self, username):
        """Генерация уникального ID для пользователя"""
        return int(hashlib.md5(username.encode()).hexdigest()[:8], 16)

    @property
    def id(self):
        return self.pk

    # Методы для совместимости
    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username