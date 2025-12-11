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


class ParameterTranslator:
    """Класс для перевода и группировки параметров"""

    @staticmethod
    def translate_parameter(param_name):
        """Перевод параметра на русский язык"""
        translations = {
            # Скорость и движение
            'Speed': 'Текущая скорость',
            'MaxSpeed': 'Максимальная скорость',
            'AverageSpeed': 'Средняя скорость',
            'SpeedLimit': 'Ограничение скорости',
            'OverspeedCount': 'Превышения скорости',
            'TotalDistance': 'Общий пробег',
            'MoveDuration': 'Время движения',
            'ParkDuration': 'Время стоянки',

            # Топливо
            'Engine1FuelConsum': 'Расход топлива',
            'TankMainFuelLevel': 'Уровень топлива',
            'TankMainFuelLevel First': 'Начальный уровень топлива',
            'TankMainFuelLevel Last': 'Конечный уровень топлива',
            'TankMainFuelUpVol Diff': 'Объем заправок',
            'TankMainFuelDnVol Diff': 'Объем слива',
            'Engine1FuelConsumMPer100km': 'Расход на 100 км',

            # Двигатель
            'Engine1Motohours': 'Моточасы',
            'Engine1MHOnParks': 'Моточасы на стоянках',
            'Engine1MHInMove': 'Моточасы в движении',
            'EngineRPM': 'Обороты двигателя',

            # Координаты
            'Longitude': 'Долгота',
            'Latitude': 'Широта',
            'Altitude': 'Высота',
            'Course': 'Направление',

            # Время
            'TotalDuration': 'Общая продолжительность',
            'WorkTime': 'Время работы',
            'IdleTime': 'Время простоя',
            'Duration': 'Длительность этапа',

            # Качество вождения
            'DQRating': 'Оценка вождения',
            'DQOverspeedPoints Diff': 'Штраф за превышение',
            'DQExcessBrakePoints Diff': 'Штраф за торможение',

            # Сигнал и датчики
            'GSMLevel': 'Уровень сигнала GSM',
            'GPSSatellites': 'Спутники GPS',
            'PowerVoltage': 'Напряжение питания',

            # CAN-данные
            'CAN_Speed': 'Скорость (CAN)',
            'CAN_RPM': 'Обороты (CAN)',

            # Общие
            'ParkCount': 'Количество остановок',
            'DT': 'Дата и время',
            'Stage': 'Этап',
            'Caption': 'Описание'
        }

        return translations.get(param_name, param_name)

    @staticmethod
    def get_unit(param_name):
        """Получение единиц измерения для параметра"""
        units = {
            # км/ч
            'Speed': 'км/ч',
            'MaxSpeed': 'км/ч',
            'AverageSpeed': 'км/ч',
            'SpeedLimit': 'км/ч',
            'CAN_Speed': 'км/ч',

            # км
            'TotalDistance': 'км',

            # л
            'Engine1FuelConsum': 'л',
            'TankMainFuelLevel': 'л',
            'TankMainFuelLevel First': 'л',
            'TankMainFuelLevel Last': 'л',
            'TankMainFuelUpVol Diff': 'л',
            'TankMainFuelDnVol Diff': 'л',

            # л/100км
            'Engine1FuelConsumMPer100km': 'л/100км',

            # ч
            'Engine1Motohours': 'ч',
            'Engine1MHOnParks': 'ч',
            'Engine1MHInMove': 'ч',
            'MoveDuration': 'ч',
            'ParkDuration': 'ч',
            'TotalDuration': 'ч',
            'WorkTime': 'ч',
            'IdleTime': 'ч',
            'Duration': 'ч',

            # %
            'DQRating': '%',

            # об/мин
            'EngineRPM': 'об/мин',
            'CAN_RPM': 'об/мин',

            # градусы
            'Longitude': '°',
            'Latitude': '°',
            'Altitude': '°',
            'Course': '°',

            # раз/шт
            'OverspeedCount': 'раз',
            'ParkCount': 'раз',
            'GPSSatellites': 'шт',

            # баллы
            'DQOverspeedPoints Diff': 'баллы',
            'DQExcessBrakePoints Diff': 'баллы',

            # В/дБ
            'PowerVoltage': 'В',
            'GSMLevel': 'дБ'
        }

        return units.get(param_name, '')

    @staticmethod
    def get_category(param_name):
        """Определение категории параметра"""
        categories = {
            'speed_motion': [
                'Speed', 'MaxSpeed', 'AverageSpeed', 'SpeedLimit',
                'OverspeedCount', 'TotalDistance', 'MoveDuration',
                'ParkDuration', 'CAN_Speed'
            ],
            'fuel': [
                'Engine1FuelConsum', 'TankMainFuelLevel',
                'TankMainFuelLevel First', 'TankMainFuelLevel Last',
                'TankMainFuelUpVol Diff', 'TankMainFuelDnVol Diff',
                'Engine1FuelConsumMPer100km'
            ],
            'engine': [
                'Engine1Motohours', 'Engine1MHOnParks', 'Engine1MHInMove',
                'EngineRPM', 'CAN_RPM'
            ],
            'coordinates': [
                'Longitude', 'Latitude', 'Altitude', 'Course'
            ],
            'time_date': [
                'TotalDuration', 'WorkTime', 'IdleTime', 'Duration',
                'DT', 'Stage', 'Caption'
            ],
            'driving_quality': [
                'DQRating', 'DQOverspeedPoints Diff',
                'DQExcessBrakePoints Diff', 'ParkCount'
            ],
            'sensors_signal': [
                'GSMLevel', 'GPSSatellites', 'PowerVoltage'
            ]
        }

        for category, params in categories.items():
            if param_name in params:
                return category

        return 'other'

    @staticmethod
    def group_parameters(param_list):
        """Группировка параметров по категориям"""
        categories = {
            'speed_motion': {
                'name': 'Скорость и движение',
                'icon': 'fa-tachometer-alt',
                'color': '#3498db',
                'params': []
            },
            'fuel': {
                'name': 'Топливо',
                'icon': 'fa-gas-pump',
                'color': '#2ecc71',
                'params': []
            },
            'engine': {
                'name': 'Двигатель',
                'icon': 'fa-cogs',
                'color': '#e74c3c',
                'params': []
            },
            'coordinates': {
                'name': 'Координаты',
                'icon': 'fa-map-marker-alt',
                'color': '#9b59b6',
                'params': []
            },
            'time_date': {
                'name': 'Время и дата',
                'icon': 'fa-clock',
                'color': '#f39c12',
                'params': []
            },
            'driving_quality': {
                'name': 'Качество вождения',
                'icon': 'fa-shield-alt',
                'color': '#1abc9c',
                'params': []
            },
            'sensors_signal': {
                'name': 'Сигнал и датчики',
                'icon': 'fa-signal',
                'color': '#e67e22',
                'params': []
            },
            'other': {
                'name': 'Прочие параметры',
                'icon': 'fa-list',
                'color': '#95a5a6',
                'params': []
            }
        }

        for param in param_list:
            category = ParameterTranslator.get_category(param)
            if category in categories:
                categories[category]['params'].append({
                    'api_name': param,
                    'display_name': ParameterTranslator.translate_parameter(param),
                    'unit': ParameterTranslator.get_unit(param),
                    'category': category
                })

        # Удаляем пустые категории
        result = {}
        for category_id, category_data in categories.items():
            if category_data['params']:
                result[category_id] = category_data

        return result


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
                'vehicles': vehicles or [],
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
                'success': True,
                'data': {
                    'historical_data': HistoricalDataFormatter.format_for_frontend({
                        'vehicles': {},
                        'summary': {},
                        'period': {'start': start_date, 'end': end_date},
                        'notes': 'Нет данных для выбранного периода'
                    }),
                    'period': {'start': start_date, 'end': end_date},
                    'vehicle_count': 0,
                    'data_type': 'empty',
                    'notes': 'Нет данных для выбранного периода'
                }
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
                'success': True,
                'data': {
                    'chart': {
                        'labels': [],
                        'datasets': []
                    },
                    'type': chart_type,
                    'param_name': param_name,
                    'note': 'Нет данных для графика'
                }
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
                'success': True,
                'data': {
                    'chart': {
                        'labels': [],
                        'datasets': []
                    },
                    'type': chart_type,
                    'param_name': param_name,
                    'note': f'Параметр {param_name} не найден'
                }
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


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_param_categories(request):
    """API: Получение категорий параметров"""
    try:
        # Категории параметров согласно спецификации
        param_categories = [
            {
                'id': 'speed_motion',
                'name': 'Скорость и движение',
                'icon': 'fa-tachometer-alt',
                'color': '#3498db',
                'param_count': 8,
                'params': [
                    {'id': 'Speed', 'name': 'Текущая скорость', 'unit': 'км/ч'},
                    {'id': 'MaxSpeed', 'name': 'Максимальная скорость', 'unit': 'км/ч'},
                    {'id': 'AverageSpeed', 'name': 'Средняя скорость', 'unit': 'км/ч'},
                    {'id': 'SpeedLimit', 'name': 'Ограничение скорости', 'unit': 'км/ч'},
                    {'id': 'OverspeedCount', 'name': 'Превышения скорости', 'unit': 'раз'},
                    {'id': 'TotalDistance', 'name': 'Общий пробег', 'unit': 'км'},
                    {'id': 'MoveDuration', 'name': 'Время движения', 'unit': 'ч'},
                    {'id': 'ParkDuration', 'name': 'Время стоянки', 'unit': 'ч'}
                ]
            },
            {
                'id': 'fuel',
                'name': 'Топливо',
                'icon': 'fa-gas-pump',
                'color': '#2ecc71',
                'param_count': 10,
                'params': [
                    {'id': 'Engine1FuelConsum', 'name': 'Расход топлива', 'unit': 'л'},
                    {'id': 'TankMainFuelLevel', 'name': 'Уровень топлива', 'unit': 'л'},
                    {'id': 'TankMainFuelLevel First', 'name': 'Начальный уровень', 'unit': 'л'},
                    {'id': 'TankMainFuelLevel Last', 'name': 'Конечный уровень', 'unit': 'л'},
                    {'id': 'TankMainFuelUpVol Diff', 'name': 'Объем заправок', 'unit': 'л'},
                    {'id': 'TankMainFuelDnVol Diff', 'name': 'Объем слива', 'unit': 'л'},
                    {'id': 'FuelConsumptionPer100km', 'name': 'Расход на 100 км', 'unit': 'л/100км'},
                    {'id': 'Engine1FuelConsumMPer100km', 'name': 'Расход на 100 км (расчетный)', 'unit': 'л/100км'},
                    {'id': 'TankMainFuelUpCount', 'name': 'Количество заправок', 'unit': 'раз'},
                    {'id': 'Engine1FuelConsumP/M', 'name': 'Расход P/M', 'unit': 'л'}
                ]
            },
            {
                'id': 'engine',
                'name': 'Двигатель',
                'icon': 'fa-cogs',
                'color': '#e74c3c',
                'param_count': 7,
                'params': [
                    {'id': 'Engine1Motohours', 'name': 'Моточасы', 'unit': 'ч'},
                    {'id': 'Engine1MHOnParks', 'name': 'Моточасы на стоянках', 'unit': 'ч'},
                    {'id': 'Engine1MHInMove', 'name': 'Моточасы в движении', 'unit': 'ч'},
                    {'id': 'EngineRPM', 'name': 'Обороты двигателя', 'unit': 'об/мин'},
                    {'id': 'EngineTemperature', 'name': 'Температура двигателя', 'unit': '°C'},
                    {'id': 'Engine1FuelConsumDuringMH', 'name': 'Расход при работе', 'unit': 'л/ч'},
                    {'id': 'Engine1FuelConsumP/MDuringMH', 'name': 'Расход P/M при работе', 'unit': 'л/ч'}
                ]
            },
            {
                'id': 'coordinates',
                'name': 'Координаты',
                'icon': 'fa-map-marker-alt',
                'color': '#9b59b6',
                'param_count': 4,
                'params': [
                    {'id': 'Longitude', 'name': 'Долгота', 'unit': '°'},
                    {'id': 'Latitude', 'name': 'Широта', 'unit': '°'},
                    {'id': 'Altitude', 'name': 'Высота', 'unit': 'м'},
                    {'id': 'Course', 'name': 'Направление', 'unit': '°'}
                ]
            },
            {
                'id': 'time_date',
                'name': 'Время и дата',
                'icon': 'fa-clock',
                'color': '#f39c12',
                'param_count': 5,
                'params': [
                    {'id': 'TotalDuration', 'name': 'Общая продолжительность', 'unit': 'ч'},
                    {'id': 'WorkTime', 'name': 'Время работы', 'unit': 'ч'},
                    {'id': 'IdleTime', 'name': 'Время простоя', 'unit': 'ч'},
                    {'id': 'DT', 'name': 'Дата и время', 'unit': ''},
                    {'id': 'Duration', 'name': 'Длительность этапа', 'unit': 'ч'}
                ]
            },
            {
                'id': 'driving_quality',
                'name': 'Качество вождения',
                'icon': 'fa-shield-alt',
                'color': '#1abc9c',
                'param_count': 9,
                'params': [
                    {'id': 'DQRating', 'name': 'Оценка вождения', 'unit': '%'},
                    {'id': 'DQOverspeedPoints Diff', 'name': 'Штраф за превышение', 'unit': 'баллы'},
                    {'id': 'DQExcessAccelPoints Diff', 'name': 'Штраф за ускорение', 'unit': 'баллы'},
                    {'id': 'DQExcessBrakePoints Diff', 'name': 'Штраф за торможение', 'unit': 'баллы'},
                    {'id': 'DQEmergencyBrakePoints Diff', 'name': 'Штраф за экстр. торможение', 'unit': 'баллы'},
                    {'id': 'DQExcessRightPoints Diff', 'name': 'Штраф за правые повороты', 'unit': 'баллы'},
                    {'id': 'DQExcessLeftPoints Diff', 'name': 'Штраф за левые повороты', 'unit': 'баллы'},
                    {'id': 'DQExcessBumpPoints Diff', 'name': 'Штраф за тряску', 'unit': 'баллы'},
                    {'id': 'DQPoints Diff', 'name': 'Всего штрафных баллов', 'unit': 'баллы'}
                ]
            },
            {
                'id': 'sensors_signal',
                'name': 'Сигнал и датчики',
                'icon': 'fa-signal',
                'color': '#e67e22',
                'param_count': 9,
                'params': [
                    {'id': 'GSMLevel', 'name': 'Уровень сигнала GSM', 'unit': 'дБ'},
                    {'id': 'GPSSatellites', 'name': 'Спутники GPS', 'unit': 'шт'},
                    {'id': 'GPSHDOP', 'name': 'Точность GPS', 'unit': ''},
                    {'id': 'PowerVoltage', 'name': 'Напряжение питания', 'unit': 'В'},
                    {'id': 'Temperature1', 'name': 'Температура 1', 'unit': '°C'},
                    {'id': 'Temperature2', 'name': 'Температура 2', 'unit': '°C'},
                    {'id': 'Temperature3', 'name': 'Температура 3', 'unit': '°C'},
                    {'id': 'Pressure1', 'name': 'Давление 1', 'unit': 'кПа'},
                    {'id': 'Pressure2', 'name': 'Давление 2', 'unit': 'кПа'}
                ]
            },
            {
                'id': 'can_data',
                'name': 'CAN-данные',
                'icon': 'fa-microchip',
                'color': '#34495e',
                'param_count': 4,
                'params': [
                    {'id': 'CAN_Speed', 'name': 'Скорость (CAN)', 'unit': 'км/ч'},
                    {'id': 'CAN_RPM', 'name': 'Обороты (CAN)', 'unit': 'об/мин'},
                    {'id': 'CAN_FuelLevel', 'name': 'Уровень топлива (CAN)', 'unit': 'л'},
                    {'id': 'CAN_OilPressure', 'name': 'Давление масла (CAN)', 'unit': 'кПа'}
                ]
            }
        ]

        return JsonResponse({
            'success': True,
            'data': {
                'categories': param_categories,
                'total_categories': len(param_categories),
                'total_params': sum(cat['param_count'] for cat in param_categories)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения категорий параметров: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_all_historical_data(request):
    """API: Получение ВСЕХ исторических данных со всеми параметрами"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        all_params = data.get('all_params', False)

        logger.info(f"Запрос ВСЕХ исторических данных: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

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

        # Получаем ВСЕ исторические данные
        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        # Форматируем даты
        start_fmt = start_date.replace('-', '')
        end_fmt = end_date.replace('-', '') + '-2359'

        # 1. Получаем данные через GetTripItems со ВСЕМИ параметрами
        logger.info("Получение ВСЕХ данных через GetTripItems...")
        trip_items_data = historical_service._get_trip_items_data_all_params(
            device_ids=vehicle_ids,
            start_fmt=start_fmt,
            end_fmt=end_fmt
        )

        # 2. Получаем обычные данные для сводки
        historical_data = historical_service.get_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data or 'vehicles' not in historical_data:
            logger.error("Исторические данные не получены или пустые")
            return JsonResponse({
                'success': True,
                'data': {
                    'historical_data': HistoricalDataFormatter.format_for_frontend({
                        'vehicles': {},
                        'summary': {},
                        'period': {'start': start_date, 'end': end_date},
                        'all_parameters': [],
                        'notes': 'Нет данных для выбранного периода'
                    }),
                    'period': {'start': start_date, 'end': end_date},
                    'vehicle_count': len(vehicle_ids),
                    'total_parameters': 0,
                    'all_parameters': [],
                    'data_type': 'empty',
                    'notes': 'Нет данных для выбранного периода'
                }
            })

        # Добавляем полные данные к каждому ТС
        all_parameters = []
        if trip_items_data:
            for device_id in vehicle_ids:
                if device_id in trip_items_data:
                    vehicle_trip_data = trip_items_data[device_id]
                    params = vehicle_trip_data.get('Params', [])
                    items = vehicle_trip_data.get('Items', [])

                    # Добавляем параметры в общий список
                    for param in params:
                        if param not in all_parameters:
                            all_parameters.append(param)

                    # Добавляем детальные данные к vehicle_data
                    if device_id in historical_data['vehicles']:
                        historical_data['vehicles'][device_id]['all_params_data'] = {
                            'params': params,
                            'items': items,
                            'item_count': len(items)
                        }
                        logger.info(f"Добавлено {len(params)} параметров для ТС {device_id}")

        historical_data['all_parameters'] = all_parameters

        # Подготавливаем данные для фронтенда
        formatted_data = HistoricalDataFormatter.format_for_frontend(historical_data)

        return JsonResponse({
            'success': True,
            'data': {
                'historical_data': formatted_data,
                'period': historical_data.get('period', {}),
                'vehicle_count': len(vehicle_ids),
                'total_parameters': len(all_parameters),
                'all_parameters': all_parameters,
                'data_type': 'full_with_all_params',
                'notes': f'Загружено {len(all_parameters)} параметров'
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения всех исторических данных: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'API_ERROR'
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_aggregated_data(request):
    """API: Получение агрегированных данных для панели анализа"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        logger.info(f"Запрос агрегированных данных: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

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
                'success': True,
                'data': {
                    'summary': {},
                    'daily_data': [],
                    'vehicle_stats': {},
                    'detailed_data': [],
                    'period': {'start': start_date, 'end': end_date}
                }
            })

        # Агрегируем данные
        aggregated_data = aggregate_historical_data(historical_data, vehicle_ids)

        return JsonResponse({
            'success': True,
            'data': aggregated_data
        })

    except Exception as e:
        logger.error(f"Ошибка получения агрегированных данных: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'API_ERROR'
        })


def aggregate_historical_data(historical_data, vehicle_ids):
    """Агрегация исторических данных для панели анализа"""
    vehicles = historical_data.get('vehicles', {})
    period = historical_data.get('period', {})

    # 1. Собираем данные по дням
    daily_data = []
    vehicle_daily_stats = {}

    # 2. Собираем статистику по ТС
    vehicle_stats = {}

    # 3. Собираем детальные данные
    detailed_data = []

    for vehicle_id, vehicle_data in vehicles.items():
        if vehicle_id not in vehicle_ids:
            continue

        vehicle_name = vehicle_data.get('name', f'ТС {vehicle_id[:8]}')

        # Инициализируем статистику ТС
        vehicle_stats[vehicle_id] = {
            'vehicle_name': vehicle_name,
            'total_distance': 0,
            'total_fuel': 0,
            'total_hours': 0,
            'trip_count': 0,
            'active_days': set(),
            'speed_values': [],
            'rating_values': []
        }

        # Обрабатываем табличные данные
        table_data = vehicle_data.get('table_data', [])
        for row in table_data:
            date = row.get('date') or row.get('dt') or ''
            if not date:
                continue

            # Извлекаем дату (без времени)
            date_only = date.split('T')[0] if 'T' in date else date.split(' ')[0]

            # Добавляем в детальные данные
            detailed_data.append({
                'vehicle_id': vehicle_id,
                'vehicle_name': vehicle_name,
                'date': date,
                'date_only': date_only,
                'distance': row.get('distance', 0),
                'fuel': row.get('fuel', 0),
                'speed': row.get('speed', 0),
                'rating': row.get('rating', 0),
                'hours': row.get('hours', 0),
                'type': row.get('type', 'unknown')
            })

            # Обновляем статистику ТС
            stats = vehicle_stats[vehicle_id]
            stats['total_distance'] += row.get('distance', 0)
            stats['total_fuel'] += row.get('fuel', 0)
            stats['total_hours'] += row.get('hours', 0)
            stats['trip_count'] += 1 if row.get('type') == 'trip' else 0
            stats['active_days'].add(date_only)

            speed = row.get('speed', 0)
            if speed:
                stats['speed_values'].append(speed)

            rating = row.get('rating', 0)
            if rating:
                stats['rating_values'].append(rating)

            # Обновляем данные по дням
            if date_only not in vehicle_daily_stats:
                vehicle_daily_stats[date_only] = {}

            if vehicle_id not in vehicle_daily_stats[date_only]:
                vehicle_daily_stats[date_only][vehicle_id] = {
                    'distance': 0,
                    'fuel': 0,
                    'hours': 0,
                    'speed_values': [],
                    'rating_values': []
                }

            day_stats = vehicle_daily_stats[date_only][vehicle_id]
            day_stats['distance'] += row.get('distance', 0)
            day_stats['fuel'] += row.get('fuel', 0)
            day_stats['hours'] += row.get('hours', 0)

            if speed:
                day_stats['speed_values'].append(speed)

            if rating:
                day_stats['rating_values'].append(rating)

    # Преобразуем данные по дням
    for date, day_vehicles in sorted(vehicle_daily_stats.items()):
        day_total_distance = 0
        day_total_fuel = 0
        day_total_hours = 0
        day_speed_values = []
        day_rating_values = []

        for vehicle_stats in day_vehicles.values():
            day_total_distance += vehicle_stats['distance']
            day_total_fuel += vehicle_stats['fuel']
            day_total_hours += vehicle_stats['hours']
            day_speed_values.extend(vehicle_stats['speed_values'])
            day_rating_values.extend(vehicle_stats['rating_values'])

        daily_data.append({
            'date': date,
            'vehicle_count': len(day_vehicles),
            'total_distance': day_total_distance,
            'total_fuel': day_total_fuel,
            'total_hours': day_total_hours,
            'avg_speed': sum(day_speed_values) / len(day_speed_values) if day_speed_values else 0,
            'avg_rating': sum(day_rating_values) / len(day_rating_values) if day_rating_values else 0
        })

    # Завершаем расчет статистики по ТС
    for vehicle_id, stats in vehicle_stats.items():
        stats['active_days'] = len(stats['active_days'])
        stats['avg_speed'] = sum(stats['speed_values']) / len(stats['speed_values']) if stats['speed_values'] else 0
        stats['avg_rating'] = sum(stats['rating_values']) / len(stats['rating_values']) if stats['rating_values'] else 0

        # Удаляем временные списки
        if 'speed_values' in stats:
            del stats['speed_values']
        if 'rating_values' in stats:
            del stats['rating_values']
        if 'active_days' in stats:
            # Уже сохранили количество, удаляем set
            del stats['active_days']

        # Добавляем количество активных дней
        stats['active_days'] = len(vehicle_stats[vehicle_id].get('active_days', set()))

    # Рассчитываем общую сводку
    total_distance = sum(stats.get('total_distance', 0) for stats in vehicle_stats.values())
    total_fuel = sum(stats.get('total_fuel', 0) for stats in vehicle_stats.values())
    total_hours = sum(stats.get('total_hours', 0) for stats in vehicle_stats.values())
    total_trips = sum(stats.get('trip_count', 0) for stats in vehicle_stats.values())

    # Рассчитываем средние значения
    vehicle_count = len(vehicle_stats)
    avg_speed = sum(
        stats.get('avg_speed', 0) for stats in vehicle_stats.values()) / vehicle_count if vehicle_count > 0 else 0
    avg_rating = sum(
        stats.get('avg_rating', 0) for stats in vehicle_stats.values()) / vehicle_count if vehicle_count > 0 else 0

    # Рассчитываем эффективность (л/100км)
    efficiency = (total_fuel / total_distance * 100) if total_distance > 0 else 0

    # Средние значения в день
    avg_daily_distance = total_distance / len(daily_data) if daily_data else 0
    avg_daily_fuel = total_fuel / len(daily_data) if daily_data else 0

    summary = {
        'total_distance': total_distance,
        'total_fuel': total_fuel,
        'total_hours': total_hours,
        'total_trips': total_trips,
        'avg_speed': avg_speed,
        'avg_rating': avg_rating,
        'efficiency': efficiency,
        'avg_daily_distance': avg_daily_distance,
        'avg_daily_fuel': avg_daily_fuel,
        'vehicle_count': vehicle_count,
        'day_count': len(daily_data)
    }

    return {
        'summary': summary,
        'daily_data': daily_data or [],
        'vehicle_stats': vehicle_stats or {},
        'detailed_data': detailed_data or [],
        'period': period
    }


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_raw_data_table(request):
    """API: Получение сырых данных для таблицы"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        logger.info(f"Запрос сырых данных для таблицы: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

        if not vehicle_ids:
            return JsonResponse({
                'success': False,
                'error': 'Не выбраны ТС',
                'code': 'NO_VEHICLES'
            })

        if not start_date or not end_date:
            return JsonResponse({
                'success': False,
                'error': 'Не указан период',
                'code': 'NO_PERIOD'
            })

        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        if not autograph_token or not schema_id:
            return JsonResponse({
                'success': False,
                'error': 'Нет подключения к AutoGRAPH',
                'code': 'NO_CONNECTION'
            })

        # Получаем данные напрямую из API
        start_fmt = start_date.replace('-', '')
        end_fmt = end_date.replace('-', '') + '-2359'

        # Используем основные параметры
        params_list = [
            "Speed", "MaxSpeed", "AverageSpeed", "TotalDistance",
            "Engine1FuelConsum", "TankMainFuelLevel", "Engine1Motohours",
            "MoveDuration", "ParkDuration", "TotalDuration", "DQRating",
            "OverspeedCount", "ParkCount", "Longitude", "Latitude",
            "EngineRPM", "PowerVoltage", "GSMLevel", "GPSSatellites"
        ]

        url = "https://web.tk-ekat.ru/ServiceJSON/GetTripItems"
        params = {
            'session': autograph_token,
            'schemaID': schema_id,
            'IDs': ','.join(vehicle_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0,
            'tripParams': ','.join(params_list)
        }

        try:
            session = requests.Session()
            session.verify = False
            response = session.get(url, params=params, timeout=90)

            if response.status_code != 200:
                logger.error(f"Ошибка API: {response.status_code}, текст: {response.text[:200]}")
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка API: {response.status_code}',
                    'code': 'API_ERROR'
                })

            raw_data = response.json()

            # Логируем структуру полученных данных
            logger.info(f"Получены данные типа: {type(raw_data)}")
            if isinstance(raw_data, dict):
                logger.info(f"Ключи в данных: {list(raw_data.keys())[:10]}...")
                for key in list(raw_data.keys())[:3]:
                    if key in vehicle_ids:
                        logger.info(f"Данные для ТС {key}: {type(raw_data[key])}")
                        if isinstance(raw_data[key], dict):
                            logger.info(f"  Параметры: {len(raw_data[key].get('Params', []))}")
                            logger.info(f"  Записи: {len(raw_data[key].get('Items', []))}")

        except Exception as e:
            logger.error(f"Ошибка запроса к AutoGRAPH: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e),
                'code': 'CONNECTION_ERROR'
            })

        if not raw_data:
            return JsonResponse({
                'success': True,
                'data': {
                    'table_data': {
                        'vehicles': {},
                        'total_records': 0,
                        'all_parameters': []
                    },
                    'parameter_groups': {},
                    'summary': {
                        'total_records': 0,
                        'total_parameters': 0,
                        'vehicle_count': 0,
                        'period': {'start': start_date, 'end': end_date}
                    }
                }
            })

        # Форматируем данные для таблицы
        table_data = format_table_data(raw_data, vehicle_ids)

        # Получаем группированные параметры
        grouped_params = ParameterTranslator.group_parameters(table_data.get('all_parameters', []))

        return JsonResponse({
            'success': True,
            'data': {
                'table_data': table_data,
                'parameter_groups': grouped_params,
                'summary': {
                    'total_records': table_data.get('total_records', 0),
                    'total_parameters': len(table_data.get('all_parameters', [])),
                    'vehicle_count': len(table_data.get('vehicles', {})),
                    'period': {'start': start_date, 'end': end_date}
                }
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения данных таблицы: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'TABLE_DATA_ERROR'
        })


def format_table_data(raw_data, vehicle_ids):
    """Форматирование данных для таблицы"""
    result = {
        'vehicles': {},
        'total_records': 0,
        'all_parameters': []
    }

    # Проверяем, что raw_data является словарем
    if not isinstance(raw_data, dict):
        logger.error(f"Ожидался словарь, получен: {type(raw_data)}")
        return result

    for device_id in vehicle_ids:
        # Приводим ID к строке для сравнения
        device_id_str = str(device_id)
        if device_id_str not in raw_data:
            logger.warning(f"ТС {device_id} не найден в данных")
            continue

        vehicle_data = raw_data[device_id_str]

        # Проверяем структуру данных
        if not isinstance(vehicle_data, dict):
            logger.warning(f"Некорректная структура данных для ТС {device_id}")
            continue

        params = vehicle_data.get('Params', [])
        items = vehicle_data.get('Items', [])

        # Получаем имя ТС (проверяем разные варианты ключей)
        vehicle_name = vehicle_data.get('Name',
                                        vehicle_data.get('name',
                                                         vehicle_data.get('DeviceName',
                                                                          f'ТС {device_id[:8]}')))

        # Добавляем параметры в общий список
        if isinstance(params, list):
            for param in params:
                if param not in result['all_parameters']:
                    result['all_parameters'].append(param)
        else:
            logger.warning(f"Params не является списком для ТС {device_id}: {type(params)}")

        # Форматируем записи (первые 100 для производительности)
        formatted_items = []
        if isinstance(items, list):
            for item in items[:100]:
                if not isinstance(item, dict):
                    continue

                formatted_item = {
                    'DT': item.get('DT', ''),
                    'Stage': item.get('Stage', ''),
                    'Duration': item.get('Duration', ''),
                    'Caption': item.get('Caption', ''),
                    'Values': {}
                }

                values = item.get('Values', [])
                if isinstance(values, list):
                    for i, param in enumerate(params):
                        if i < len(values):
                            formatted_item['Values'][param] = values[i]

                formatted_items.append(formatted_item)
        else:
            logger.warning(f"Items не является списком для ТС {device_id}: {type(items)}")

        result['vehicles'][device_id] = {
            'name': vehicle_name,
            'params': params if isinstance(params, list) else [],
            'items_count': len(items) if isinstance(items, list) else 0,
            'samples': formatted_items
        }

        result['total_records'] += len(items) if isinstance(items, list) else 0

    return result