from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
import os

def home_view(request):
    return HttpResponse(f"""
    <h1>🚗 Транспортная компания</h1>
    <p>Сайт успешно запущен на Render!</p>
    <p><strong>DEBUG:</strong> {__import__('django.conf').settings.DEBUG}</p>
    <p><strong>Host:</strong> {request.get_host()}</p>
    <p><strong>Path:</strong> {request.path}</p>
    <hr>
    <p><a href="/auth/login/">Войти в систему</a></p>
    <p><a href="/admin/">Админка</a></p>
    <p><a href="/health/">Health Check</a></p>
    <hr>
    <p>Статус: Работает ✅</p>
    """)

def health_check(request):
    return HttpResponse("OK", status=200)

urlpatterns = [
    path('', home_view, name='home'),
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/vehicles/', include('vehicles.urls')),
]