# vehicles/html_urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicles, name='vehicles'),
    path('charts/', views.vehicle_charts, name='vehicle_charts'),
    path('analytics/', views.analytics_page, name='vehicles_analytics'),
    path('statistics-page/', views.statistics_page, name='vehicles_statistics_page'),
    path('api-test/', views.api_test_page, name='vehicles_api_test'),
]