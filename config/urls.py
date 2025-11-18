# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView


def home_view(request):
    """Главная страница - редирект на вход"""
    return RedirectView.as_view(url='/auth/login/', permanent=False)(request)


def health_check(request):
    return HttpResponse("OK", status=200)


urlpatterns = [
    path('', home_view, name='home'),
    path('health/', health_check, name='health_check'),
    path('auth/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('reports/', include('reports.urls')),# И HTML и API через префиксы
]