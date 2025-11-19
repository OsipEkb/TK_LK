# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .services import AutoGraphDashboardService
import logging

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """ОСНОВНОЙ дашборд"""
    try:
        service = AutoGraphDashboardService()
        dashboard_data = service.get_dashboard_data()

        if dashboard_data:
            context = {
                'schema_name': dashboard_data.get('schema_name', 'Osipenko'),
                'total_vehicles': dashboard_data.get('total_vehicles', 0),
                'vehicles': dashboard_data.get('vehicles', []),
                'current_time': timezone.now(),
            }
        else:
            context = {
                'schema_name': 'Osipenko',
                'total_vehicles': 0,
                'vehicles': [],
                'current_time': timezone.now(),
            }

        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        logger.error(f"Dashboard view error: {e}")
        context = {
            'schema_name': 'Osipenko',
            'total_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
        }
        return render(request, 'dashboard/dashboard.html', context)


@login_required
def dashboard_api(request):
    """API для получения данных дашборда"""
    try:
        logger.info("🚀 DASHBOARD API CALLED")

        service = AutoGraphDashboardService()
        dashboard_data = service.get_dashboard_data()

        if dashboard_data:
            logger.info(f"✅ Dashboard data received: {len(dashboard_data.get('vehicles', []))} vehicles")

            return JsonResponse({
                'success': True,
                'data': dashboard_data
            })
        else:
            logger.error("❌ No dashboard data received")
            return JsonResponse({
                'success': False,
                'error': 'Не удалось получить данные дашборда'
            })

    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        })


@login_required
def vehicle_detail_api(request, vehicle_id):
    """API для получения детальной информации по ТС"""
    try:
        service = AutoGraphDashboardService()
        vehicle_data = service.get_vehicle_details(vehicle_id)

        if vehicle_data:
            return JsonResponse({
                'success': True,
                'data': vehicle_data
            })
        else:
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


@login_required
def vehicles_page(request):
    """Страница транспорта"""
    return render(request, 'vehicles/vehicles.html', {
        'all_vehicles': [],
        'schema_name': 'Osipenko',
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