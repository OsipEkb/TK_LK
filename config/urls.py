from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView

def home_view(request):
    return HttpResponse("""
    <h1>🚗 Транспортная компания "Техноком"</h1>
    <p>Система управления транспортом</p>
    <hr>
    <p><a href="/auth/login/">📱 Войти в систему</a></p>
    <p><a href="/admin/">⚙️ Админка</a></p>
    <p><a href="/health/">❤️ Health Check</a></p>
    <hr>
    <p>Статус: <strong>Работает ✅</strong></p>
    <p>Сервер: <strong>Render</strong></p>
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