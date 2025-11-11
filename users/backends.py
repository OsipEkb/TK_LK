from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from app.api.clients import AutoGraphAPIClient
import logging

logger = logging.getLogger(__name__)


class AutoGraphAuthBackend(BaseBackend):
    """Бэкенд аутентификации через AutoGRAPH API"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            client = AutoGraphAPIClient()
            token = client.login(username, password)

            if token:
                User = get_user_model()

                # Получаем схемы для получения информации об организации
                schemas = client.enum_schemas()
                organization_name = schemas[0]['Name'] if schemas else 'Default'

                # Создаем или получаем организацию
                from .models import Organization
                organization, _ = Organization.objects.get_or_create(
                    name=organization_name,
                    defaults={'external_id': organization_name}
                )

                # Создаем или получаем пользователя
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f"{username}@tehnokom.com",
                        'external_id': username,
                        'organization': organization,
                        'user_type': 'user',
                    }
                )

                # Обновляем организацию если нужно
                if not created and user.organization != organization:
                    user.organization = organization
                    user.save()

                # Сохраняем токен в сессии для API запросов
                request.session['autograph_token'] = token
                request.session['autograph_username'] = username

                logger.info(f"User {username} authenticated successfully")
                return user

        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")

        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None