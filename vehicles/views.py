# vehicles/views.py - добавьте эти функции

from django.shortcuts import render
from datetime import datetime, timedelta

def vehicles_dashboard(request):
    """Основная страница мониторинга транспорта"""
    context = {
        'page_title': 'Мониторинг транспорта',
        'default_start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d'),
        'current_time': datetime.now()
    }
    return render(request, 'vehicles/dashboard.html', context)


def vehicle_detail(request, vehicle_id):
    """Детальная страница транспортного средства"""
    context = {
        'page_title': f'Транспорт #{vehicle_id}',
        'vehicle_id': vehicle_id,
        'default_start_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d')
    }
    return render(request, 'vehicles/vehicle_detail.html', context)


def analytics_page(request):
    """Страница аналитики"""
    context = {
        'page_title': 'Аналитика транспорта',
        'default_start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d')
    }
    return render(request, 'vehicles/analytics.html', context)


def enhanced_analytics_page(request):
    """Страница расширенной аналитики"""
    context = {
        'page_title': 'Расширенная аналитика',
        'default_start_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'default_end_date': datetime.now().strftime('%Y-%m-%d'),
        'current_time': datetime.now()
    }
    return render(request, 'vehicles/analytics_enhanced.html', context)