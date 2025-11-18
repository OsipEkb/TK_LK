from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@login_required
def reports_page(request):
    """Главная страница отчетов"""
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=30)

    context = {
        'default_start_date': default_start_date.strftime('%Y-%m-%d'),
        'default_end_date': default_end_date.strftime('%Y-%m-%d'),
        'current_time': timezone.now(),
    }

    return render(request, 'reports/reports.html', context)