"""
URL configuration for TK_LK project.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def redirect_to_dashboard(request):
    """Перенаправление с корня на дашборд"""
    return redirect('/dashboard/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_dashboard, name='home'),
    path('auth/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('vehicles/', include('vehicles.urls')),
]