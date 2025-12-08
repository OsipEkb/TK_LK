# vehicles/views.py
import json
import logging
from datetime import datetime, timedelta
import requests
import warnings

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from functools import wraps

from .services import AutoGraphHistoricalService, AutoGraphDeviceService

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
logger = logging.getLogger(__name__)


class HistoricalDataFormatter:
    """Класс для форматирования исторических данных"""

    @staticmethod
    def format_for_frontend(historical_data):
        """Форматирование данных для фронтенда (СТАРЫЙ ФОРМАТ для совместимости)"""
        if not historical_data:
            return {
                'vehicles': {},
                'summary': {},
                'chart_data': {},
                'total_stages': 0,
                'data_type': 'stage_based',
                'notes': 'Нет данных'
            }

        formatted = {
            'vehicles': {},
            'summary': historical_data.get('summary', {}),
            'chart_data': historical_data.get('chart_data', {}),
            'raw_data': historical_data.get('raw_data', {}),
            'total_stages': historical_data.get('total_stages', 0),
            'available_parameters': historical_data.get('available_parameters', []),
            'period': historical_data.get('period', {}),
            'data_type': historical_data.get('data_type', 'stage_based'),
            'sources': historical_data.get('sources', []),
            'notes': historical_data.get('notes', '')
        }

        vehicles = historical_data.get('vehicles', {})

        for vehicle_id, vehicle_data in vehicles.items():
            # Получаем данные из разных источников
            trips_only_stats = vehicle_data.get('trips_only_stats', {})
            trip_items_stats = vehicle_data.get('trip_items_stats', {})
            summary = vehicle_data.get('summary', {})

            # Формируем данные для фронтенда (СТАРЫЙ ФОРМАТ)
            formatted['vehicles'][vehicle_id] = {
                'id': vehicle_id,
                'name': vehicle_data.get('name', ''),
                'summary': summary,
                'statistics': trip_items_stats.get('statistics', {}),
                'stage_count': trip_items_stats.get('stage_count', 0),
                'trip_count': trips_only_stats.get('trip_count', 0),

                # Данные для таблицы (старый формат)
                'table_data': HistoricalDataFormatter._prepare_table_data_old_format(
                    trips_only_stats, trip_items_stats
                ),

                # Данные для графиков (старый формат)
                'chart_data': HistoricalDataFormatter._prepare_chart_data_old_format(
                    trip_items_stats, vehicle_data.get('name', '')
                ),

                # Сырые данные стадий (первые 50 для отображения)
                'stages_sample': trip_items_stats.get('raw_stages', [])[:50],

                # Статистика для отображения
                'summary_corrected': {
                    'total_distance': round(summary.get('distance', 0), 2),
                    'total_fuel': round(summary.get('fuel', 0), 2),
                    'avg_speed': round(summary.get('avg_speed', 0), 2),
                    'avg_rating': 0,  # Можно вычислить если есть данные
                    'total_hours': round(summary.get('motohours', 0), 2),
                    'move_duration': round(summary.get('move_duration', 0), 2),
                    'park_duration': round(summary.get('park_duration', 0), 2)
                }
            }

        return formatted

    @staticmethod
    def _prepare_table_data_old_format(trips_only_stats: dict, trip_items_stats: dict) -> list:
        """Подготовка данных для таблицы в старом формате"""
        table_data = []

        # Добавляем поездки
        for trip in trips_only_stats.get('trips', []):
            table_data.append({
                'type': 'trip',
                'date': trip.get('date', ''),
                'start_time': trip.get('start_time', ''),
                'distance': round(trip.get('distance', 0), 2),
                'speed': round(trip.get('avg_speed', 0), 2),
                'fuel': round(trip.get('fuel', 0), 2),
                'rating': 0,
                'hours': round(trip.get('motohours', 0), 2),
                'stages': ''
            })

        # Если нет поездок, добавляем данные из стадий
        if not table_data:
            for stage in trip_items_stats.get('raw_stages', [])[:100]:
                table_data.append({
                    'type': 'stage',
                    'date': stage.get('date', ''),
                    'dt': stage.get('dt', ''),
                    'distance': round(stage.get('TotalDistance', 0), 2),
                    'speed': round(stage.get('AverageSpeed', 0), 2),
                    'fuel': round(stage.get('Engine1FuelConsum', 0), 2),
                    'rating': round(stage.get('DQRating', 0), 2),
                    'hours': round(stage.get('Engine1Motohours', 0), 2),
                    'stages': stage.get('stage', '')
                })

        return table_data

    @staticmethod
    def _prepare_chart_data_old_format(trip_items_stats: dict, vehicle_name: str) -> dict:
        """Подготовка данных для графиков в старом формате"""
        chart_data = {
            'daily': [],
            'parameters': {}
        }

        # Группируем данные по дням
        daily_data = {}
        for stage in trip_items_stats.get('raw_stages', []):
            date = stage.get('date')
            if not date:
                continue

            if date not in daily_data:
                daily_data[date] = {
                    'date': date,
                    'distance': 0,
                    'fuel': 0,
                    'speed': [],
                    'rating': []
                }

            daily_data[date]['distance'] += stage.get('TotalDistance', 0)
            daily_data[date]['fuel'] += stage.get('Engine1FuelConsum', 0)

            speed = stage.get('AverageSpeed', 0)
            if speed:
                daily_data[date]['speed'].append(speed)

            rating = stage.get('DQRating', 0)
            if rating:
                daily_data[date]['rating'].append(rating)

        # Формируем данные для графика
        for date, data in sorted(daily_data.items()):
            avg_speed = sum(data['speed']) / len(data['speed']) if data['speed'] else 0
            avg_rating = sum(data['rating']) / len(data['rating']) if data['rating'] else 0

            chart_data['daily'].append({
                'date': date,
                'distance': round(data['distance'], 2),
                'fuel': round(data['fuel'], 2),
                'avg_speed': round(avg_speed, 2),
                'avg_rating': round(avg_rating, 2),
                'stage_count': len([s for s in trip_items_stats.get('raw_stages', [])
                                    if s.get('date') == date])
            })

        return chart_data


class ChartDataProcessor:
    """Класс для обработки данных графиков"""

    @staticmethod
    def get_parameter_groups():
        """Получение групп параметров для графиков"""
        return {
            'basic': {
                'name': 'Основные показатели',
                'icon': 'fa-chart-line',
                'color': '#3498db',
                'parameters': [
                    {'api_name': 'TotalDistance', 'display_name': 'Пробег', 'unit': 'км'},
                    {'api_name': 'AverageSpeed', 'display_name': 'Средняя скорость', 'unit': 'км/ч'},
                    {'api_name': 'MaxSpeed', 'display_name': 'Макс. скорость', 'unit': 'км/ч'},
                    {'api_name': 'TotalDuration', 'display_name': 'Общее время', 'unit': 'ч'},
                    {'api_name': 'MoveDuration', 'display_name': 'Время движения', 'unit': 'ч'},
                    {'api_name': 'ParkDuration', 'display_name': 'Время стоянки', 'unit': 'ч'}
                ]
            },
            'fuel': {
                'name': 'Топливо',
                'icon': 'fa-gas-pump',
                'color': '#2ecc71',
                'parameters': [
                    {'api_name': 'Engine1FuelConsum', 'display_name': 'Расход топлива', 'unit': 'л'},
                    {'api_name': 'Engine1FuelConsumMPer100km', 'display_name': 'Расход на 100км', 'unit': 'л/100км'},
                    {'api_name': 'TankMainFuelLevel First', 'display_name': 'Топливо на начало', 'unit': 'л'},
                    {'api_name': 'TankMainFuelLevel Last', 'display_name': 'Топливо на конец', 'unit': 'л'},
                    {'api_name': 'TankMainFuelUpVol Diff', 'display_name': 'Заправки', 'unit': 'л'},
                    {'api_name': 'TankMainFuelDnVol Diff', 'display_name': 'Сливы', 'unit': 'л'}
                ]
            },
            'engine': {
                'name': 'Двигатель',
                'icon': 'fa-cogs',
                'color': '#e74c3c',
                'parameters': [
                    {'api_name': 'Engine1Motohours', 'display_name': 'Моточасы', 'unit': 'ч'},
                    {'api_name': 'Engine1MHOnParks', 'display_name': 'Моточасы на стоянке', 'unit': 'ч'},
                    {'api_name': 'Engine1MHInMove', 'display_name': 'Моточасы в движении', 'unit': 'ч'}
                ]
            },
            'safety': {
                'name': 'Безопасность и рейтинг',
                'icon': 'fa-shield-alt',
                'color': '#f39c12',
                'parameters': [
                    {'api_name': 'DQRating', 'display_name': 'Рейтинг вождения', 'unit': '%'},
                    {'api_name': 'OverspeedCount', 'display_name': 'Превышения скорости', 'unit': 'раз'},
                    {'api_name': 'ParkCount', 'display_name': 'Остановки', 'unit': 'раз'},
                    {'api_name': 'DQOverspeedPoints Diff', 'display_name': 'Баллы за превышение', 'unit': 'баллы'},
                    {'api_name': 'DQExcessBrakePoints Diff', 'display_name': 'Баллы за торможение', 'unit': 'баллы'}
                ]
            }
        }


# Кастомный декоратор для проверки токена AutoGRAPH
def autograph_token_required(view_func):
    """Декоратор для проверки токена AutoGRAPH"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        autograph_token = request.session.get('autograph_token')

        if not autograph_token:
            logger.warning(f"🔒 No AutoGRAPH token for {request.path}")
            return JsonResponse({
                'success': False,
                'error': 'Требуется авторизация в AutoGRAPH',
                'code': 'NO_AUTH'
            })

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def vehicles_main(request):
    """Главная страница анализа исторических данных"""
    autograph_token = request.session.get('autograph_token')
    schema_id = request.session.get('autograph_schema_id')
    schema_name = request.session.get('autograph_schema_name')

    if not autograph_token or not schema_id:
        return render(request, 'vehicles/error.html', {
            'error': 'Требуется авторизация в AutoGRAPH'
        })

    context = {
        'page_title': 'Анализ исторических данных ТС',
        'default_start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d'),
        'autograph_username': request.session.get('autograph_username'),
        'schema_name': schema_name,
        'schema_id': schema_id,
        'has_autograph_token': bool(autograph_token)
    }

    return render(request, 'vehicles/vehicles.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_vehicles(request):
    """API: Получение списка ТС"""
    try:
        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        if not autograph_token or not schema_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет подключения к AutoGRAPH'
            })

        service = AutoGraphDeviceService(token=autograph_token)
        devices = service.get_devices(schema_id)

        logger.info(f"Получено устройств: {len(devices)}")

        vehicles = []
        for device in devices:
            vehicles.append({
                "id": device['id'],
                "name": device['name'],
                "license_plate": device.get('reg_num', ''),
                "serial": device.get('serial', ''),
                "model": device.get('model', ''),
                "driver": device.get('driver', '')
            })

        return JsonResponse({
            'success': True,
            'data': {
                'vehicles': vehicles,
                'count': len(vehicles)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения ТС: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_historical_data(request):
    """API: Получение исторических данных (СОВМЕСТИМЫЙ ФОРМАТ)"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        logger.info(f"Запрос исторических данных: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

        if not vehicle_ids:
            logger.warning("Не выбраны ТС")
            return JsonResponse({
                'success': False,
                'error': 'Не выбраны ТС',
                'code': 'NO_VEHICLES'
            })

        if not start_date or not end_date:
            logger.warning("Не указан период")
            return JsonResponse({
                'success': False,
                'error': 'Не указан период',
                'code': 'NO_PERIOD'
            })

        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        if not autograph_token or not schema_id:
            logger.warning("Нет подключения к AutoGRAPH")
            return JsonResponse({
                'success': False,
                'error': 'Нет подключения к AutoGRAPH',
                'code': 'NO_CONNECTION'
            })

        # Получаем исторические данные
        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        historical_data = historical_service.get_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data or 'vehicles' not in historical_data:
            logger.error("Исторические данные не получены или пустые")
            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить данные из AutoGRAPH',
                'code': 'DATA_FETCH_ERROR'
            })

        # Подготавливаем данные для фронтенда (СТАРЫЙ ФОРМАТ)
        formatted_data = HistoricalDataFormatter.format_for_frontend(historical_data)

        return JsonResponse({
            'success': True,
            'data': {
                'historical_data': formatted_data,
                'period': historical_data.get('period', {}),
                'vehicle_count': len(vehicle_ids),
                'data_type': historical_data.get('data_type', 'stage_based'),
                'notes': historical_data.get('notes', ''),
                'request_details': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'vehicle_ids_count': len(vehicle_ids)
                }
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения исторических данных: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'API_ERROR'
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_parameter_groups(request):
    """API: Получение групп параметров для графиков"""
    try:
        parameter_groups = ChartDataProcessor.get_parameter_groups()

        # Полный список всех параметров
        all_params = []
        for group in parameter_groups.values():
            all_params.extend([param['api_name'] for param in group['parameters']])

        return JsonResponse({
            'success': True,
            'data': {
                'groups': parameter_groups,
                'all_parameters': all_params,
                'total_parameters': len(all_params)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения групп параметров: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_chart_data(request):
    """API: Получение данных для конкретного графика"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_id = data.get('vehicle_id')
        chart_id = data.get('chart_id')
        chart_type = data.get('chart_type', 'bar')
        param_name = data.get('param_name')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not vehicle_id or not param_name:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны обязательные параметры'
            })

        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        if not autograph_token or not schema_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет подключения к AutoGRAPH'
            })

        # Получаем сырые данные для графика
        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        # Форматируем даты
        start_fmt = start_date.replace('-', '') if start_date else '20250101'
        end_fmt = end_date.replace('-', '') + '-2359' if end_date else '20251231-2359'

        # Получаем данные через GetTripItems
        trip_items_data = historical_service._get_trip_items_data(
            device_ids=[vehicle_id],
            start_fmt=start_fmt,
            end_fmt=end_fmt,
            stage='Motion'
        )

        if not trip_items_data or vehicle_id not in trip_items_data:
            return JsonResponse({
                'success': False,
                'error': 'Нет данных для графика'
            })

        # Обрабатываем данные для графика
        vehicle_data = trip_items_data[vehicle_id]
        items = vehicle_data.get('Items', [])
        params = vehicle_data.get('Params', [])

        # Находим индекс параметра
        param_index = -1
        for i, param in enumerate(params):
            if param == param_name:
                param_index = i
                break

        if param_index == -1:
            return JsonResponse({
                'success': False,
                'error': f'Параметр {param_name} не найден'
            })

        # Группируем данные по дням
        daily_data = {}
        for item in items:
            dt = item.get('DT', '')
            if not dt:
                continue

            # Извлекаем дату
            date_key = ''
            if 'T' in dt:
                date_key = dt.split('T')[0]
            elif ' ' in dt:
                date_key = dt.split(' ')[0]
            else:
                date_key = dt[:10] if len(dt) >= 10 else dt

            if not date_key:
                continue

            values = item.get('Values', [])
            if param_index < len(values):
                value = values[param_index]
                num_value = historical_service._parse_numeric_value(value)

                if num_value is not None:
                    if date_key not in daily_data:
                        daily_data[date_key] = []
                    daily_data[date_key].append(num_value)

        # Создаем данные для графика
        chart_data = {
            'labels': [],
            'datasets': [{
                'label': param_name,
                'data': [],
                'backgroundColor': '#FFD700' if chart_type == 'bar' else 'transparent',
                'borderColor': '#FFD700',
                'borderWidth': 2
            }]
        }

        for date, values in sorted(daily_data.items()):
            if values:
                avg_value = sum(values) / len(values)
                chart_data['labels'].append(date)
                chart_data['datasets'][0]['data'].append(round(avg_value, 2))

        return JsonResponse({
            'success': True,
            'data': {
                'chart': chart_data,
                'type': chart_type,
                'param_name': param_name
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения данных графика: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_export_data(request):
    """API: Экспорт данных в CSV"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        export_type = data.get('type', 'csv')
        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not vehicle_ids or not start_date or not end_date:
            return JsonResponse({
                'success': False,
                'error': 'Не указаны обязательные параметры'
            })

        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        if not autograph_token or not schema_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет подключения к AutoGRAPH'
            })

        # Получаем данные
        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        historical_data = historical_service.get_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data:
            return JsonResponse({
                'success': False,
                'error': 'Нет данных для экспорта'
            })

        # Генерируем CSV
        csv_data = "ТС;Дата;Тип;Пробег (км);Скорость (км/ч);Расход (л);Рейтинг (%);Моточасы (ч);Стадии\n"

        for vehicle_id, vehicle_data in historical_data.get('vehicles', {}).items():
            vehicle_name = vehicle_data.get('name', '')

            # Экспортируем данные из таблицы
            for row in HistoricalDataFormatter._prepare_table_data_old_format(
                    vehicle_data.get('trips_only_stats', {}),
                    vehicle_data.get('trip_items_stats', {})
            ):
                csv_data += f'"{vehicle_name}";'
                csv_data += f'"{row.get("date", row.get("dt", ""))}";'
                csv_data += f'"{row.get("type", "")}";'
                csv_data += f'{row.get("distance", 0)};'
                csv_data += f'{row.get("speed", 0)};'
                csv_data += f'{row.get("fuel", 0)};'
                csv_data += f'{row.get("rating", 0)};'
                csv_data += f'{row.get("hours", 0)};'
                csv_data += f'"{row.get("stages", "")}"\n'

        filename = f"данные-тс-{start_date}_{end_date}.csv"

        return JsonResponse({
            'success': True,
            'data': {
                'filename': filename,
                'content': csv_data,
                'type': 'csv',
                'size': len(csv_data)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка экспорта данных: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })