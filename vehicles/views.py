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


class AdvancedDataFormatter:
    """Класс для форматирования данных с временными рядами"""

    @staticmethod
    def format_for_timeseries(historical_data):
        """Форматирование данных для временных рядов"""
        if not historical_data:
            return {
                'time_series': [],
                'summary': {},
                'parameters': [],
                'total_records': 0,
                'period': {'start': '', 'end': ''}
            }

        # Проверяем тип данных и форматируем соответствующим образом
        if historical_data.get('data_type') in ['time_series_extended', 'fallback_basic', 'empty']:
            # Новый формат из get_extended_historical_data
            return {
                'time_series': historical_data.get('time_series', []),
                'summary': historical_data.get('summary', {}),
                'parameters': historical_data.get('parameters', []),
                'total_records': historical_data.get('total_records', 0),
                'period': historical_data.get('period', {}),
                'vehicle_count': len(historical_data.get('vehicle_info', {}))
            }
        elif 'vehicles' in historical_data:
            # Старый формат для совместимости
            time_series = []
            all_parameters = set()

            available_params = historical_data.get('available_parameters', [])
            for param in available_params:
                all_parameters.add(param)

            for vehicle_id, vehicle_data in historical_data['vehicles'].items():
                vehicle_name = vehicle_data.get('name', f'ТС {vehicle_id[:8]}')

                if 'stages_sample' in vehicle_data:
                    for stage in vehicle_data['stages_sample']:
                        time_point = {
                            'timestamp': stage.get('dt', stage.get('date', '')),
                            'vehicle': vehicle_name,
                            'vehicle_id': vehicle_id,
                            'type': 'stage',
                            'stage': stage.get('stage', ''),
                            'values': {}
                        }

                        for key, value in stage.items():
                            if isinstance(value, (int, float)) or (
                                    isinstance(value, str) and value.replace('.', '', 1).isdigit()):
                                time_point['values'][key] = float(value)
                                all_parameters.add(key)

                        time_series.append(time_point)

                if 'table_data' in vehicle_data:
                    for row in vehicle_data['table_data']:
                        timestamp = row.get('dt', row.get('date', row.get('start_time', '')))
                        if not timestamp:
                            continue

                        time_point = {
                            'timestamp': timestamp,
                            'vehicle': vehicle_name,
                            'vehicle_id': vehicle_id,
                            'type': row.get('type', 'data'),
                            'values': {}
                        }

                        numeric_fields = ['distance', 'speed', 'fuel', 'rating', 'hours']
                        for field in numeric_fields:
                            if field in row:
                                time_point['values'][field.capitalize()] = float(row[field])
                                all_parameters.add(field.capitalize())

                        for key, value in row.items():
                            if key not in ['dt', 'date', 'start_time', 'vehicle', 'type', 'stage']:
                                if isinstance(value, (int, float)) or (
                                        isinstance(value, str) and value.replace('.', '', 1).isdigit()):
                                    time_point['values'][key] = float(value)
                                    all_parameters.add(key)

                        time_series.append(time_point)

            time_series.sort(key=lambda x: x['timestamp'])

            return {
                'time_series': time_series,
                'summary': historical_data.get('summary', {}),
                'parameters': sorted(list(all_parameters)),
                'total_records': len(time_series),
                'period': historical_data.get('period', {}),
                'vehicle_count': len(historical_data.get('vehicles', {}))
            }
        else:
            # Неизвестный формат
            return {
                'time_series': [],
                'summary': {},
                'parameters': [],
                'total_records': 0,
                'period': historical_data.get('period', {}),
                'vehicle_count': 0
            }

    @staticmethod
    def get_extended_parameter_list():
        """Получение расширенного списка параметров с переводами"""
        return [
            {'id': 'Speed', 'name': 'Текущая скорость', 'unit': 'км/ч', 'category': 'speed'},
            {'id': 'MaxSpeed', 'name': 'Максимальная скорость', 'unit': 'км/ч', 'category': 'speed'},
            {'id': 'AverageSpeed', 'name': 'Средняя скорость', 'unit': 'км/ч', 'category': 'speed'},
            {'id': 'TotalDistance', 'name': 'Общий пробег', 'unit': 'км', 'category': 'distance'},
            {'id': 'MoveDuration', 'name': 'Время движения', 'unit': 'ч', 'category': 'time'},
            {'id': 'ParkDuration', 'name': 'Время стоянки', 'unit': 'ч', 'category': 'time'},
            {'id': 'ParkCount', 'name': 'Количество остановок', 'unit': 'раз', 'category': 'events'},
            {'id': 'Engine1FuelConsum', 'name': 'Расход топлива', 'unit': 'л', 'category': 'fuel'},
            {'id': 'TankMainFuelLevel', 'name': 'Уровень топлива', 'unit': 'л', 'category': 'fuel'},
            {'id': 'Engine1FuelConsumMPer100km', 'name': 'Расход на 100 км', 'unit': 'л/100км', 'category': 'fuel'},
            {'id': 'Engine1Motohours', 'name': 'Моточасы', 'unit': 'ч', 'category': 'engine'},
            {'id': 'EngineRPM', 'name': 'Обороты двигателя', 'unit': 'об/мин', 'category': 'engine'},
            {'id': 'DQRating', 'name': 'Рейтинг вождения', 'unit': '%', 'category': 'safety'},
            {'id': 'OverspeedCount', 'name': 'Превышения скорости', 'unit': 'раз', 'category': 'safety'},
            {'id': 'Longitude', 'name': 'Долгота', 'unit': '°', 'category': 'location'},
            {'id': 'Latitude', 'name': 'Широта', 'unit': '°', 'category': 'location'},
            {'id': 'GSMLevel', 'name': 'Уровень сигнала GSM', 'unit': 'дБ', 'category': 'signal'},
            {'id': 'GPSSatellites', 'name': 'Спутники GPS', 'unit': 'шт', 'category': 'signal'},
            {'id': 'PowerVoltage', 'name': 'Напряжение питания', 'unit': 'В', 'category': 'signal'},
        ]


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

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    context = {
        'page_title': 'Анализ данных ТС',
        'default_start_date': start_date.strftime('%Y-%m-%d'),
        'default_end_date': end_date.strftime('%Y-%m-%d'),
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
def api_get_all_historical_data(request):
    """API: Получение ВСЕХ исторических данных для временных рядов"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        all_params = data.get('all_params', True)

        logger.info(f"Запрос расширенных данных: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

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

        # Получаем исторические данные через обновленный сервис
        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        historical_data = historical_service.get_extended_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data:
            logger.error("Исторические данные не получены или пустые")
            return JsonResponse({
                'success': True,
                'data': {
                    'historical_data': {
                        'time_series': [],
                        'summary': {
                            'total_records': 0,
                            'vehicle_count': 0,
                            'time_range': {'start': start_date, 'end': end_date}
                        },
                        'parameters': [],
                        'total_records': 0,
                        'period': {'start': start_date, 'end': end_date},
                        'data_type': 'empty'
                    }
                }
            })

        # Форматируем данные для фронтенда
        formatted_data = AdvancedDataFormatter.format_for_timeseries(historical_data)

        return JsonResponse({
            'success': True,
            'data': {
                'historical_data': formatted_data,
                'period': historical_data.get('period', {'start': start_date, 'end': end_date}),
                'vehicle_count': len(vehicle_ids),
                'total_records': formatted_data.get('total_records', 0)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения расширенных данных: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'API_ERROR'
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_parameters_list(request):
    """API: Получение списка параметров с переводами"""
    try:
        parameters = AdvancedDataFormatter.get_extended_parameter_list()

        categories = {}
        for param in parameters:
            category = param['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(param)

        return JsonResponse({
            'success': True,
            'data': {
                'parameters': parameters,
                'categories': categories,
                'total_parameters': len(parameters)
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения списка параметров: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_get_time_series_data(request):
    """API: Получение данных временных рядов для конкретных параметров"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        params = data.get('params', [])
        resolution = data.get('resolution', 'minute')

        logger.info(f"Запрос временных рядов: {len(params)} параметров, resolution={resolution}")

        if not vehicle_ids or not params:
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

        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        historical_data = historical_service.get_extended_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data:
            return JsonResponse({
                'success': True,
                'data': {
                    'time_series': [],
                    'parameters': params,
                    'resolution': resolution
                }
            })

        formatted_data = AdvancedDataFormatter.format_for_timeseries(historical_data)

        aggregated_data = aggregate_time_series(formatted_data['time_series'], params, resolution)

        return JsonResponse({
            'success': True,
            'data': {
                'time_series': aggregated_data,
                'parameters': params,
                'resolution': resolution,
                'summary': formatted_data['summary']
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения данных временных рядов: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def aggregate_time_series(time_series, params, resolution):
    """Агрегация временных рядов по разрешению"""
    if not time_series:
        return []

    intervals = {}

    for point in time_series:
        timestamp = point.get('timestamp')
        if not timestamp:
            continue

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            continue

        if resolution == 'hour':
            interval_key = dt.strftime('%Y-%m-%d %H:00:00')
        elif resolution == 'day':
            interval_key = dt.strftime('%Y-%m-%d')
        else:
            interval_key = dt.strftime('%Y-%m-%d %H:%M:00')

        if interval_key not in intervals:
            intervals[interval_key] = {
                'timestamp': interval_key,
                'values': {param: [] for param in params},
                'count': 0
            }

        values = point.get('values', {})
        for param in params:
            if param in values:
                intervals[interval_key]['values'][param].append(values[param])

        intervals[interval_key]['count'] += 1

    result = []
    for interval_key, data in intervals.items():
        aggregated_point = {
            'timestamp': data['timestamp'],
            'values': {}
        }

        for param, values_list in data['values'].items():
            if values_list:
                avg_value = sum(values_list) / len(values_list)
                aggregated_point['values'][param] = round(avg_value, 4)

        result.append(aggregated_point)

    result.sort(key=lambda x: x['timestamp'])

    return result


@csrf_exempt
@require_http_methods(["POST"])
@autograph_token_required
def api_export_time_series(request):
    """API: Экспорт данных временных рядов"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        export_format = data.get('format', 'csv')
        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        params = data.get('params', [])

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

        historical_service = AutoGraphHistoricalService(
            token=autograph_token,
            schema_id=schema_id
        )

        historical_data = historical_service.get_extended_historical_data(
            device_ids=vehicle_ids,
            start_date=start_date,
            end_date=end_date
        )

        if not historical_data:
            return JsonResponse({
                'success': False,
                'error': 'Нет данных для экспорта'
            })

        formatted_data = AdvancedDataFormatter.format_for_timeseries(historical_data)

        if export_format == 'csv':
            csv_data = generate_time_series_csv(formatted_data['time_series'], params)
            filename = f"временные-ряды-{start_date}_{end_date}.csv"

            return JsonResponse({
                'success': True,
                'data': {
                    'filename': filename,
                    'content': csv_data,
                    'format': 'csv',
                    'size': len(csv_data)
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'data': {
                    'time_series': formatted_data['time_series'],
                    'summary': formatted_data['summary'],
                    'format': 'json'
                }
            })

    except Exception as e:
        logger.error(f"Ошибка экспорта временных рядов: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def generate_time_series_csv(time_series, params):
    """Генерация CSV из данных временных рядов"""
    if not time_series:
        return "Нет данных"

    headers = ['Время', 'ТС', 'Тип']
    headers.extend(params)

    rows = []
    for point in time_series:
        row = [
            point.get('timestamp', ''),
            point.get('vehicle', point.get('vehicle_name', '')),
            point.get('type', point.get('stage', ''))
        ]

        values = point.get('values', {})
        for param in params:
            value = values.get(param, '')
            if isinstance(value, (int, float)):
                value = f"{value:.4f}"
            row.append(str(value))

        rows.append(row)

    csv_lines = [','.join(headers)]
    csv_lines.extend([','.join(row) for row in rows])

    return '\n'.join(csv_lines)


@csrf_exempt
@require_http_methods(["POST"])
def api_get_system_status(request):
    """API: Проверка статуса системы"""
    try:
        autograph_token = request.session.get('autograph_token')
        schema_id = request.session.get('autograph_schema_id')

        status = {
            'autograph_connected': bool(autograph_token and schema_id),
            'schema_name': request.session.get('autograph_schema_name'),
            'username': request.session.get('autograph_username'),
            'timestamp': datetime.now().isoformat()
        }

        return JsonResponse({
            'success': True,
            'data': status
        })

    except Exception as e:
        logger.error(f"Ошибка проверки статуса: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })