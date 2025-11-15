from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .services import AutoGraphDashboardService  # ИМПОРТИРУЕМ ИЗ ТЕКУЩЕЙ ДИРЕКТОРИИ
import logging
from datetime import datetime, timedelta
import dateutil.parser

logger = logging.getLogger(__name__)


def format_last_update(timestamp):
    """Форматирование времени последнего обновления"""
    if not timestamp:
        return {
            'text': "Нет данных",
            'status': "offline",
            'full': "Нет данных"
        }

    try:
        # Используем timezone-aware datetime для текущего времени
        now = timezone.now()

        # Парсим timestamp в timezone-aware datetime
        if isinstance(timestamp, (int, float)):
            # Unix timestamp (предполагаем миллисекунды)
            if timestamp > 1e10:  # Если число слишком большое, это вероятно миллисекунды
                dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        elif isinstance(timestamp, str):
            # Строковый формат - используем dateutil для надежного парсинга
            if 'T' in timestamp:
                # ISO format с timezone
                dt = dateutil.parser.isoparse(timestamp)
                # Если нет timezone, считаем UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Другие форматы - парсим как наивное время и добавляем UTC
                dt = datetime.strptime(timestamp, '%Y%m%d-%H%M%S')
                dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(timestamp, datetime):
            # Если уже datetime
            dt = timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            return {
                'text': "Неизвестный формат",
                'status': "offline",
                'full': str(timestamp)
            }

        # Убедимся, что оба времени в одном часовом поясе
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt)

        # Теперь можем безопасно вычитать
        time_diff = now - dt

        if time_diff < timedelta(minutes=5):
            status = "online"
            time_text = "только что"
        elif time_diff < timedelta(hours=1):
            status = "online"
            minutes = int(time_diff.total_seconds() / 60)
            time_text = f"{minutes} мин назад"
        elif time_diff < timedelta(hours=24):
            status = "warning"
            hours = int(time_diff.total_seconds() / 3600)
            time_text = f"{hours} ч назад"
        else:
            status = "offline"
            days = time_diff.days
            time_text = f"{days} дн назад"

        return {
            'text': time_text,
            'status': status,
            'full': dt.astimezone(timezone.get_current_timezone()).strftime('%d.%m.%Y %H:%M:%S')
        }

    except Exception as e:
        logger.error(f"Error formatting timestamp {timestamp}: {e}")
        return {
            'text': "Ошибка времени",
            'status': "offline",
            'full': str(timestamp)
        }


@method_decorator(login_required, name='dispatch')
class DashboardDataAPI(View):
    """API для получения данных дашборда"""

    def get(self, request):
        try:
            print("🚀 DASHBOARD API CALLED")
            service = AutoGraphDashboardService()  # ИСПОЛЬЗУЕМ НАШ НОВЫЙ СЕРВИС
            if service.login("Osipenko", "Osipenko"):
                schemas = service.get_schemas()
                if schemas:
                    schema_id = schemas[0].get('ID')

                    # ИСПОЛЬЗУЕМ УЛУЧШЕННЫЙ МЕТОД
                    print("🔄 Calling get_enhanced_dashboard_summary...")
                    dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                    if dashboard_data:
                        print("✅ Enhanced dashboard data received")
                        # Обрабатываем данные о времени и формируем ответ
                        processed_data = self.process_dashboard_data(dashboard_data)
                        return JsonResponse({
                            'success': True,
                            'data': processed_data
                        })
                    else:
                        print("❌ No dashboard data received")
                        return JsonResponse({
                            'success': False,
                            'error': 'Не удалось получить данные дашборда'
                        })

            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить данные от AutoGRAPH'
            })

        except Exception as e:
            logger.error(f"Dashboard API error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            })

    def process_dashboard_data(self, dashboard_data):
        """Обработка данных дашборда для API"""
        processed_data = dashboard_data.copy()

        # Обрабатываем каждое ТС для форматирования времени
        for vehicle in processed_data.get('vehicles', []):
            if vehicle.get('last_update'):
                vehicle['last_update_formatted'] = format_last_update(vehicle['last_update'])
            else:
                vehicle['last_update_formatted'] = {
                    'text': 'Нет данных',
                    'status': 'offline',
                    'full': 'Нет данных о времени'
                }

            # Добавляем дополнительную информацию для отображения
            vehicle['is_moving'] = vehicle.get('speed', 0) > 0

        return processed_data


@method_decorator(login_required, name='dispatch')
class VehicleDetailAPI(View):
    """API для получения детальной информации по ТС"""

    def get(self, request, vehicle_id):
        try:
            service = AutoGraphDashboardService()  # ИСПОЛЬЗУЕМ НАШ НОВЫЙ СЕРВИС
            if service.login("Osipenko", "Osipenko"):
                schemas = service.get_schemas()
                if schemas:
                    schema_id = schemas[0].get('ID')

                    # Получаем детальную информацию о ТС
                    detailed_info = service.get_vehicle_detailed_info(schema_id, vehicle_id)

                    if detailed_info:
                        return JsonResponse({
                            'success': True,
                            'data': detailed_info
                        })

            return JsonResponse({
                'success': False,
                'error': 'ТС не найдено'
            })

        except Exception as e:
            logger.error(f"Vehicle detail API error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка получения данных: {str(e)}'
            })