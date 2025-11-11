from celery import shared_task
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
from .services import VehicleDataService
import logging

logger = logging.getLogger(__name__)


@shared_task
def refresh_vehicles_data_for_all_users():
    """Периодическое обновление данных всех пользователей"""
    try:
        User = get_user_model()
        active_users = User.objects.filter(is_active=True)

        updated_count = 0
        error_count = 0

        for user in active_users:
            try:
                service = VehicleDataService(user)
                schemas = service.get_available_schemas()

                for schema in schemas:
                    schema_id = schema['id']
                    # Используем принудительное обновление
                    service.refresh_all_data(schema_id)
                    updated_count += 1
                    logger.info(f"✅ Updated data for user {user.username}, schema {schema_id}")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error updating data for user {user.username}: {e}")
                continue

        logger.info(f"🔄 Data refresh completed. Updated: {updated_count}, Errors: {error_count}")
        return {
            'updated_count': updated_count,
            'error_count': error_count,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"💥 Critical error in refresh task: {e}")
        return {'error': str(e)}


@shared_task
def refresh_user_vehicles_data(user_id, schema_id=None):
    """Обновление данных для конкретного пользователя"""
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id, is_active=True)

        service = VehicleDataService(user)

        if schema_id:
            # Обновляем конкретную схему
            result = service.refresh_all_data(schema_id)
            logger.info(f"✅ Updated schema {schema_id} for user {user.username}")
            return {'user': user.username, 'schema': schema_id, 'status': 'success'}
        else:
            # Обновляем все схемы пользователя
            schemas = service.get_available_schemas()
            for schema in schemas:
                service.refresh_all_data(schema['id'])
            logger.info(f"✅ Updated all schemas for user {user.username}")
            return {'user': user.username, 'schemas_count': len(schemas), 'status': 'success'}

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error updating data for user {user_id}: {e}")
        return {'error': str(e)}