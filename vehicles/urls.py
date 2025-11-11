# vehicles/urls.py
from django.urls import path
from .api_views import VehiclesListAPI, VehicleChartDataAPI

urlpatterns = [
    path('', VehiclesListAPI.as_view(), name='api_vehicles_list'),  # /api/vehicles/
    path('chart-data/', VehicleChartDataAPI.as_view(), name='api_vehicle_chart_data'),  # /api/vehicles/chart-data/
]