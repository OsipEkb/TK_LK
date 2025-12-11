from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicles_main, name='vehicles_main'),

    # API endpoints
    path('api/get-vehicles/', views.api_get_vehicles, name='api_get_vehicles'),
    path('api/get-all-historical-data/', views.api_get_all_historical_data, name='api_get_all_historical_data'),
    path('api/get-parameters-list/', views.api_get_parameters_list, name='api_get_parameters_list'),
    path('api/get-time-series-data/', views.api_get_time_series_data, name='api_get_time_series_data'),
    path('api/export-time-series/', views.api_export_time_series, name='api_export_time_series'),
    path('api/get-system-status/', views.api_get_system_status, name='api_get_system_status'),
]