from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from users.views import HTMLLoginView


# Простая заглушка для главной страницы
def home_view(request):
    return HttpResponse("""
    <h1>🚗 Транспортная компания</h1>
    <p>Сайт успешно запущен на Render!</p>
    <p><a href="/auth/login/">Войти в систему</a></p>
    <p><a href="/admin/">Админка</a></p>
    <hr>
    <p>Статус: Работает ✅</p>
    """)


urlpatterns = [
    path('admin/', admin.site.urls),

    # ВРЕМЕННО: простая главная страница
    path('', home_view, name='home'),

    # Authentication URLs
    path('auth/', include('users.urls')),

    # API routes
    path('api/vehicles/', include('vehicles.urls')),

    # HTML routes
    path('dashboard/', include('dashboard.urls')),
]