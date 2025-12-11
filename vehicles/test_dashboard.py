"""
Тестовая панель с диаграммами и сырыми данными
"""

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from datetime import datetime, timedelta
from .services import AutoGraphDeviceService

logger = logging.getLogger(__name__)


def test_dashboard_view(request):
    """Тестовая панель с диаграммами"""
    autograph_token = request.session.get('autograph_token')
    schema_id = request.session.get('autograph_schema_id')

    if not autograph_token or not schema_id:
        return render(request, 'vehicles/error.html', {
            'error': 'Требуется авторизация в AutoGRAPH'
        })

    context = {
        'page_title': 'Тестовая панель с данными',
        'default_start_date': '2025-12-03',
        'default_end_date': '2025-12-10',
        'autograph_username': request.session.get('autograph_username'),
        'schema_name': request.session.get('autograph_schema_name'),
        'schema_id': schema_id,
        'has_autograph_token': bool(autograph_token),
        'is_test_dashboard': True
    }

    return render(request, 'vehicles/test_dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_test_get_raw_data(request):
    """API: Получение ВСЕХ сырых данных напрямую из AutoGRAPH"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        logger.info(f"Запрос сырых данных: vehicles={len(vehicle_ids)}, period={start_date} - {end_date}")

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

        # Форматируем даты для API
        start_fmt = start_date.replace('-', '')
        end_fmt = end_date.replace('-', '') + '-2359'

        # Получаем данные напрямую из AutoGRAPH API
        raw_data = get_raw_data_from_autograph(
            autograph_token, schema_id, vehicle_ids, start_fmt, end_fmt
        )

        if not raw_data:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить данные из AutoGRAPH',
                'code': 'DATA_FETCH_ERROR'
            })

        # Форматируем для фронтенда
        formatted_data = format_raw_data_for_frontend(
            raw_data, vehicle_ids, start_date, end_date
        )

        return JsonResponse({
            'success': True,
            'data': formatted_data,
            'request_info': {
                'vehicle_count': len(vehicle_ids),
                'start_date': start_date,
                'end_date': end_date,
                'total_records': formatted_data['total_records']
            }
        })

    except Exception as e:
        logger.error(f"Ошибка получения сырых данных: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'code': 'RAW_DATA_ERROR'
        })


def get_raw_data_from_autograph(token, schema_id, vehicle_ids, start_fmt, end_fmt):
    """Прямой запрос к AutoGRAPH API"""

    # Основные параметры для получения
    params_list = [
        "Speed", "MaxSpeed", "AverageSpeed", "TotalDistance",
        "Engine1FuelConsum", "TankMainFuelLevel", "Engine1Motohours",
        "MoveDuration", "ParkDuration", "TotalDuration", "DQRating",
        "OverspeedCount", "ParkCount", "Longitude", "Latitude",
        "EngineRPM", "PowerVoltage", "GSMLevel", "GPSSatellites",
        "Temperature1", "Temperature2", "Temperature3",
        "TankMainFuelLevel First", "TankMainFuelLevel Last",
        "TankMainFuelUpVol Diff", "TankMainFuelDnVol Diff",
        "DQOverspeedPoints Diff", "DQExcessBrakePoints Diff",
        "DQExcessAccelPoints Diff", "DQEmergencyBrakePoints Diff"
    ]

    url = "https://web.tk-ekat.ru/ServiceJSON/GetTripItems"

    # Попробуем сначала со всеми параметрами
    try:
        params = {
            'session': token,
            'schemaID': schema_id,
            'IDs': ','.join(vehicle_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0,
            'tripParams': '*',  # Пробуем получить ВСЕ параметры
            'tripTotalParams': '*'
        }

        session = requests.Session()
        session.verify = False
        session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'TestDashboard/1.0'
        })

        logger.info(f"Запрос всех параметров: {url}")
        response = session.get(url, params=params, timeout=120)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Получены все параметры для {len(data)} ТС")
            return data
        else:
            logger.warning(f"❌ Ошибка со всеми параметрами: {response.status_code}")

    except Exception as e:
        logger.warning(f"❌ Ошибка запроса всех параметров: {e}")

    # Если не получилось со всеми, пробуем с основными
    try:
        params = {
            'session': token,
            'schemaID': schema_id,
            'IDs': ','.join(vehicle_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0,
            'tripParams': ','.join(params_list)
        }

        session = requests.Session()
        session.verify = False

        logger.info(f"Запрос основных параметров: {len(params_list)} шт")
        response = session.get(url, params=params, timeout=90)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Получены основные параметры для {len(data)} ТС")
            return data

    except Exception as e:
        logger.error(f"❌ Ошибка запроса основных параметров: {e}")

    return None


def format_raw_data_for_frontend(raw_data, vehicle_ids, start_date, end_date):
    """Форматирование сырых данных для фронтенда"""
    result = {
        'vehicles': {},
        'total_records': 0,
        'all_parameters': [],
        'period': {
            'start': start_date,
            'end': end_date
        },
        'timezone_info': {
            'server_time': datetime.now().isoformat(),
            'utc_offset': '+05:00'
        }
    }

    for device_id in vehicle_ids:
        if device_id not in raw_data:
            logger.warning(f"ТС {device_id} не найден в данных")
            continue

        vehicle_data = raw_data[device_id]
        params = vehicle_data.get('Params', [])
        items = vehicle_data.get('Items', [])

        # Получаем имя ТС
        vehicle_name = vehicle_data.get('Name', f'ТС {device_id[:8]}')

        # Собираем все параметры
        for param in params:
            if param not in result['all_parameters']:
                result['all_parameters'].append(param)

        # Форматируем записи (первые 100 для производительности)
        formatted_items = []
        for item in items[:100]:
            formatted_item = {
                'DT': item.get('DT', ''),
                'Stage': item.get('Stage', ''),
                'Duration': item.get('Duration', ''),
                'Caption': item.get('Caption', ''),
                'Values': {}
            }

            values = item.get('Values', [])
            for i, param in enumerate(params):
                if i < len(values):
                    formatted_item['Values'][param] = values[i]

            formatted_items.append(formatted_item)

        result['vehicles'][device_id] = {
            'name': vehicle_name,
            'params': params,
            'items_count': len(items),
            'samples': formatted_items,
            'params_sample': params[:20]  # Первые 20 параметров для отображения
        }

        result['total_records'] += len(items)

    # Сортируем параметры по алфавиту
    result['all_parameters'].sort()

    logger.info(f"✅ Обработано данных: {result['total_records']} записей, {len(result['all_parameters'])} параметров")

    return result


@csrf_exempt
@require_http_methods(["POST"])
def api_test_get_charts(request):
    """API: Простые графики для сравнения"""
    try:
        data = json.loads(request.body.decode('utf-8'))

        vehicle_ids = data.get('vehicle_ids', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not vehicle_ids or not start_date or not end_date:
            return JsonResponse({'success': False, 'error': 'Не указаны параметры'})

        # Простые демо-данные для графика
        chart_data = create_simple_chart_data(vehicle_ids, start_date, end_date)

        return JsonResponse({
            'success': True,
            'data': chart_data
        })

    except Exception as e:
        logger.error(f"Ошибка создания графиков: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def create_simple_chart_data(vehicle_ids, start_date, end_date):
    """Создание простых данных для графика"""
    return {
        'type': 'line',
        'labels': ['День 1', 'День 2', 'День 3', 'День 4', 'День 5', 'День 6', 'День 7'],
        'datasets': [
            {
                'label': 'Средняя скорость (км/ч)',
                'data': [45, 52, 48, 55, 50, 47, 53],
                'borderColor': '#FFD700',
                'backgroundColor': 'rgba(255, 215, 0, 0.1)'
            },
            {
                'label': 'Расход топлива (л)',
                'data': [120, 135, 125, 140, 130, 128, 138],
                'borderColor': '#3498db',
                'backgroundColor': 'rgba(52, 152, 219, 0.1)'
            }
        ]
    }