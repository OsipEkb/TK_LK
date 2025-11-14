# vehicles/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta


@login_required
def vehicles(request):
    """Главная страница транспорта - ДЛЯ ИСТОРИЧЕСКОГО АНАЛИЗА"""
    # Устанавливаем даты по умолчанию для исторического анализа
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=30)  # 30 дней для анализа

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
        'current_time': datetime.now(),
        'page_title': 'Исторические данные транспорта',
        'analysis_period': '30 дней'
    }

    return render(request, 'vehicles/vehicles.html', context)


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