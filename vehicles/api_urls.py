# vehicles/api_urls.py
from django.urls import path
from .api_views import (
    VehiclesListAPI,
    VehicleChartDataAPI,
    VehicleHistoricalDataAPI,
    VehicleStatisticsAPI
)

urlpatterns = [
    path('', VehiclesListAPI.as_view(), name='api_vehicles_list'),
    path('chart-data/', VehicleChartDataAPI.as_view(), name='api_vehicle_chart_data'),
    path('historical-data/', VehicleHistoricalDataAPI.as_view(), name='api_vehicle_historical_data'),
    path('statistics/', VehicleStatisticsAPI.as_view(), name='api_vehicle_statistics'),
]