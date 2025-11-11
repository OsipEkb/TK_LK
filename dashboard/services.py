# dashboard/services.py (дополняем)
import redis
import json
from django.conf import settings
from datetime import datetime


class DataCacheService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.CACHES['default']['LOCATION']
        ) if settings.CELERY_BROKER_URL else None

    def cache_dashboard_data(self, user_id, data):
        """Кэшируем данные дашборда для пользователя"""
        if self.redis_client:
            key = f"dashboard_data_{user_id}"
            self.redis_client.setex(
                key,
                settings.DATA_REFRESH_INTERVAL,
                json.dumps(data)
            )

    def get_cached_dashboard_data(self, user_id):
        """Получаем кэшированные данные"""
        if self.redis_client:
            key = f"dashboard_data_{user_id}"
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        return None