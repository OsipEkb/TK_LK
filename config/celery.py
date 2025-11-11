from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Расписание для автоматического обновления данных
app.conf.beat_schedule = {
    'refresh-vehicles-data-every-5-minutes': {
        'task': 'vehicles.tasks.refresh_vehicles_data_for_all_users',
        'schedule': 300.0,  # 5 минут
    },
    'clean-old-cache-every-hour': {
        'task': 'vehicles.tasks.clean_old_cache',
        'schedule': 3600.0,  # 1 час
    },
}

app.conf.timezone = 'Europe/Moscow'