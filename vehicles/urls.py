# vehicles/urls.py
from django.urls import path
from .api_views import (
    VehiclesListAPI,
    VehicleChartDataAPI,
    VehicleHistoricalDataAPI,
    VehicleStatisticsAPI
)
from . import views

urlpatterns = [
    # HTML страницы
    path('', views.vehicles, name='vehicles'),
    path('<str:vehicle_id>/dashboard/', views.vehicle_dashboard, name='vehicle_dashboard'),
    path('charts/', views.vehicle_charts, name='vehicle_charts'),
    path('analytics/', views.analytics_page, name='vehicles_analytics'),
    path('statistics-page/', views.statistics_page, name='vehicles_statistics_page'),
    path('api-test/', views.api_test_page, name='vehicles_api_test'),

    # API endpoints
    path('api/list/', VehiclesListAPI.as_view(), name='api_vehicles_list'),
    path('api/chart-data/', VehicleChartDataAPI.as_view(), name='api_vehicle_chart_data'),
    path('api/historical-data/', VehicleHistoricalDataAPI.as_view(), name='api_vehicle_historical_data'),
    path('api/statistics/', VehicleStatisticsAPI.as_view(), name='api_vehicle_statistics'),
]