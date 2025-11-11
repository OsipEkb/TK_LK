from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import AutoGraphService
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta


@login_required
def vehicles(request):
    """Страница с интерактивными графиками транспорта"""
    # Устанавливаем даты по умолчанию
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=7)

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'vehicle.html', context)


@csrf_exempt
def get_schemas(request):
    """Получение списка схем"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            service = AutoGraphService()
            if service.login(username, password):
                schemas = service.get_schemas()
                return JsonResponse({'schemas': schemas, 'success': True})
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_vehicles(request, schema_id):
    """Получение ТС в схеме"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            service = AutoGraphService()
            if service.login(username, password):
                vehicles_data = service.get_vehicles(schema_id)
                return JsonResponse({'vehicles': vehicles_data, 'success': True})
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_vehicle_parameters(request, schema_id, device_id):
    """Получение доступных параметров для ТС"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            service = AutoGraphService()
            if service.login(username, password):
                parameters = service.get_vehicle_parameters(schema_id, device_id)
                return JsonResponse({'parameters': parameters, 'success': True})
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_vehicle_chart_data(request, schema_id, device_id):
    """Получение данных для графиков ТС"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            parameters = data.get('parameters', [])  # Список параметров для графиков

            service = AutoGraphService()
            if service.login(username, password):
                # Форматируем даты для API
                start_date_formatted = service.format_date_for_api(start_date)
                end_date_formatted = service.format_date_for_api(end_date)

                # Получаем данные для графиков
                chart_data = service.get_trip_tables(
                    schema_id,
                    device_id,
                    start_date_formatted,
                    end_date_formatted,
                    parameters
                )

                return JsonResponse({
                    'chart_data': chart_data,
                    'success': True,
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                })
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_vehicle_trips_summary(request, schema_id, device_id):
    """Получение сводки по рейсам ТС"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            service = AutoGraphService()
            if service.login(username, password):
                # Форматируем даты для API
                start_date_formatted = service.format_date_for_api(start_date)
                end_date_formatted = service.format_date_for_api(end_date)

                # Получаем суммарные данные по рейсам
                trips_data = service.get_trips_total(
                    schema_id,
                    device_id,
                    start_date_formatted,
                    end_date_formatted
                )

                return JsonResponse({
                    'trips_summary': trips_data,
                    'success': True
                })
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_vehicle_track(request, schema_id, device_id):
    """Получение трека ТС"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            service = AutoGraphService()
            if service.login(username, password):
                # Форматируем даты для API
                start_date_formatted = service.format_date_for_api(start_date, include_time=True)
                end_date_formatted = service.format_date_for_api(end_date, include_time=True)

                track_data = service.get_track_data(
                    schema_id,
                    device_id,
                    start_date_formatted,
                    end_date_formatted
                )

                return JsonResponse({
                    'track_data': track_data,
                    'success': True
                })
            else:
                return JsonResponse({'error': 'Authentication failed', 'success': False}, status=401)

        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def vehicle_charts(request):
    """Страница с интерактивными графиками транспорта"""
    from datetime import datetime, timedelta

    # Устанавливаем даты по умолчанию
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=7)

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'vehicle_charts.html', context)