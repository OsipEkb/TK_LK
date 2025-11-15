from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .services import AutoGraphDashboardService  # ИМПОРТИРУЕМ ИЗ ТЕКУЩЕЙ ДИРЕКТОРИИ
import logging

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """ОСНОВНОЙ дашборд с улучшенными данными (включая топливо)"""
    try:
        service = AutoGraphDashboardService()  # ИСПОЛЬЗУЕМ НАШ НОВЫЙ СЕРВИС
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')
                schema_name = schemas[0].get('Name', 'Основная схема')

                # ИСПОЛЬЗУЕМ УЛУЧШЕННЫЙ МЕТОД С ТОПЛИВОМ
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                if dashboard_data:
                    context = {
                        'schema_name': schema_name,
                        'total_vehicles': dashboard_data.get('total_vehicles', 0),
                        'online_vehicles': dashboard_data.get('online_vehicles', 0),
                        'offline_vehicles': dashboard_data.get('offline_vehicles', 0),
                        'moving_vehicles': len([v for v in dashboard_data.get('vehicles', []) if v.get('speed', 0) > 0]),
                        'vehicles': dashboard_data.get('vehicles', []),
                        'current_time': timezone.now(),
                        'last_update': dashboard_data.get('last_update'),
                        'vehicles_with_fuel': len([v for v in dashboard_data.get('vehicles', []) if v.get('fuel_level') is not None]),
                    }
                else:
                    context = {
                        'schema_name': schema_name,
                        'total_vehicles': 0,
                        'online_vehicles': 0,
                        'offline_vehicles': 0,
                        'moving_vehicles': 0,
                        'vehicles': [],
                        'current_time': timezone.now(),
                        'vehicles_with_fuel': 0,
                    }

                return render(request, 'dashboard/dashboard.html', context)

        # Fallback если сервис недоступен
        context = {
            'schema_name': 'Основная схема',
            'total_vehicles': 0,
            'online_vehicles': 0,
            'offline_vehicles': 0,
            'moving_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
            'vehicles_with_fuel': 0,
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
            'vehicles_with_fuel': 0,
        }
        return render(request, 'dashboard/dashboard.html', context)


# Остальные view функции остаются без изменений, но используют новый сервис
@login_required
def vehicles_page(request):
    """Страница транспорта - теперь использует исторические данные из vehicles/services.py"""
    # Эта функция теперь должна использовать vehicles/services.py
    # Оставляем как есть или можно удалить если не используется
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