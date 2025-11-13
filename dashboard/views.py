# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from vehicles.services import AutoGraphService
import logging

logger = logging.getLogger(__name__)


def extract_license_plate(vehicle_data):
    """Извлечение госномера из свойств ТС"""
    try:
        properties = vehicle_data.get('properties', [])
        for prop in properties:
            if prop.get('name') in ['LicensePlate', 'Госномер', 'Номер']:
                return prop.get('value', '')
        return vehicle_data.get('Name', '')
    except:
        return vehicle_data.get('Name', '')


@login_required
def dashboard(request):
    """Стартовая страница дашборда с автообновлением"""
    try:
        # Получаем данные для первоначальной загрузки страницы
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                first_schema = schemas[0]
                schema_id = first_schema.get('ID')

                # Получаем данные для шаблона
                dashboard_data = service.get_dashboard_summary(schema_id)

                if dashboard_data:
                    # Считаем ТС в движении для первоначального отображения
                    moving_vehicles = len([v for v in dashboard_data.get('vehicles', []) if v.get('speed', 0) > 0])

                    context = {
                        'schema_name': first_schema.get('Name', 'Основная схема'),
                        'total_vehicles': dashboard_data.get('total_vehicles', 0),
                        'online_vehicles': dashboard_data.get('online_vehicles', 0),
                        'offline_vehicles': dashboard_data.get('offline_vehicles', 0),
                        'moving_vehicles': moving_vehicles,
                        'vehicles': dashboard_data.get('vehicles', []),
                        'current_time': timezone.now(),
                    }
                    return render(request, 'dashboard/dashboard.html', context)

        # Fallback если данные не получены
        context = {
            'schema_name': 'Основная схема',
            'total_vehicles': 0,
            'online_vehicles': 0,
            'offline_vehicles': 0,
            'moving_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
        }
        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        logger.error(f"Dashboard view error: {e}")
        context = {
            'schema_name': 'Основная схема',
            'total_vehicles': 0,
            'online_vehicles': 0,
            'offline_vehicles': 0,
            'moving_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
        }
        return render(request, 'dashboard/dashboard.html', context)


@login_required
def debug_online(request):
    """Страница для отладки онлайн данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем сырые данные для отладки
                online_data = service.debug_online_data(schema_id)

                context = {
                    'online_data': online_data,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                    'current_time': timezone.now(),
                }
                return render(request, 'dashboard/debug_online.html', context)

    except Exception as e:
        logger.error(f"Debug error: {e}")

    return render(request, 'dashboard/debug_online.html', {
        'online_data': {},
        'schema_name': 'Основная схема',
        'current_time': timezone.now(),
    })


@login_required
def vehicles_page(request):
    """Страница транспорта с реальными данными"""
    try:
        # Используем реальные credentials для получения данных
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                first_schema = schemas[0]
                schema_id = first_schema.get('ID')
                schema_name = first_schema.get('Name', 'Основная схема')

                vehicles_data = service.get_vehicles(schema_id)
                all_vehicles = []

                if vehicles_data and 'Items' in vehicles_data:
                    for item in vehicles_data['Items']:
                        vehicle = {
                            'id': item.get('ID'),
                            'name': item.get('Name', 'Без названия'),
                            'license_plate': extract_license_plate(item),
                            'serial': item.get('Serial'),
                            'allowed': item.get('Allowed', False),
                        }
                        all_vehicles.append(vehicle)

                context = {
                    'all_vehicles': all_vehicles,
                    'schema_name': schema_name,
                    'current_time': timezone.now(),
                }
                return render(request, 'vehicles/vehicles.html', context)

        # Если что-то пошло не так
        return render(request, 'vehicles/vehicles.html', {
            'all_vehicles': [],
            'schema_name': 'Основная схема',
            'current_time': timezone.now(),
        })

    except Exception as e:
        logger.error(f"Ошибка получения данных транспорта: {e}")
        return render(request, 'vehicles/vehicles.html', {
            'all_vehicles': [],
            'schema_name': 'Основная схема',
            'current_time': timezone.now(),
        })


@login_required
def reports(request):
    return render(request, 'reports/reports.html')


@login_required
def retransmission(request):
    return render(request, 'retransmission/retransmission.html')


@login_required
def billing(request):
    return render(request, 'billing/billing.html')


@login_required
def support(request):
    return render(request, 'support/support.html')