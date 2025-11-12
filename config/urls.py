from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import HTMLLoginView  # Импортируем ваш класс-based view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Главная страница теперь ведет на HTML форму входа
    path('', HTMLLoginView.as_view(), name='home'),

    # Authentication URLs
    path('auth/', include('users.urls')),

    # API routes
    path('api/vehicles/', include('vehicles.urls')),

    # HTML routes
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)