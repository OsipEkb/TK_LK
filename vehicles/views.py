# vehicles/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@login_required
def vehicles_page(request):
    """Главная страница транспорта - использует реальные данные из AutoGRAPH"""
    try:
        # Используем сервис для получения реальных данных
        from .services import AutoGraphService

        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем список всех ТС
                vehicles_data = service.get_vehicles(schema_id)

                # Обрабатываем данные для отображения
                all_vehicles = []
                if vehicles_data and 'Items' in vehicles_data:
                    for vehicle in vehicles_data['Items']:
                        # Извлекаем госномер
                        license_plate = service.extract_license_plate_enhanced(vehicle)

                        all_vehicles.append({
                            'id': vehicle.get('ID'),
                            'name': vehicle.get('Name', 'Unknown'),
                            'license_plate': license_plate,
                            'serial': vehicle.get('Serial'),
                            'schema_id': schema_id
                        })

                context = {
                    'all_vehicles': all_vehicles,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                    'current_time': timezone.now(),
                    'total_vehicles': len(all_vehicles),
                    'default_start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'default_end_date': datetime.now().strftime('%Y-%m-%d')
                }

                return render(request, 'vehicles/vehicles.html', context)

    except Exception as e:
        logger.error(f"Vehicles page error: {e}")

    # Fallback
    return render(request, 'vehicles/vehicles.html', {
        'all_vehicles': [],
        'schema_name': 'Основная схема',
        'current_time': timezone.now(),
        'total_vehicles': 0,
        'default_start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d')
    })


@login_required
def vehicle_dashboard(request, vehicle_id):
    """Дашборд конкретного ТС с историческими данными"""
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=7)

    context = {
        'vehicle_id': vehicle_id,
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
        'current_time': datetime.now(),
    }

    return render(request, 'vehicles/vehicle_dashboard.html', context)


@login_required
def vehicle_charts(request):
    """Страница с интерактивными графиками исторических данных"""
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=30)

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
    }

    return render(request, 'vehicles/vehicle_charts.html', context)


@login_required
def analytics_page(request):
    """Страница аналитики исторических данных транспорта"""
    return render(request, 'vehicles/analytics.html')


@login_required
def statistics_page(request):
    """Страница для просмотра исторической статистики транспорта"""
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=7)

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_start_time': '00:00',
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
        'default_end_time': '23:59',
    }

    return render(request, 'vehicles/statistics.html', context)


@login_required
def api_test_page(request):
    """Страница для тестирования API исторических данных"""
    return render(request, 'vehicles/api_test.html')


@login_required
def debug_dashboard(request):
    """Страница визуальной диагностики"""
    return render(request, 'vehicles/debug_dashboard.html')


@login_required
def data_collection_page(request):
    """Страница для управления сбором данных"""
    return render(request, 'vehicles/data_collection.html')


@login_required
def debug_dashboard(request):
    """Страница диагностики AutoGRAPH API"""
    return render(request, 'vehicles/debug.html')


@login_required
def debug_historical(request):
    """Страница диагностики исторических данных"""
    return render(request, 'vehicles/debug_historical.html')