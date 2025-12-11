# В vehicles/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicles_main, name='vehicles_main'),

    # Основные API endpoints
    path('api/get-vehicles/', views.api_get_vehicles, name='api_get_vehicles'),
    path('api/get-historical-data/', views.api_get_historical_data, name='api_get_historical_data'),
    path('api/get-parameter-groups/', views.api_get_parameter_groups, name='api_get_parameter_groups'),
    path('api/get-param-categories/', views.api_get_param_categories, name='api_get_param_categories'),
    path('api/get-aggregated-data/', views.api_get_aggregated_data, name='api_get_aggregated_data'),
    path('api/get-all-historical-data/', views.api_get_all_historical_data, name='api_get_all_historical_data'),

    # Новые API для таблицы с группировкой параметров
    path('api/get-raw-data-table/', views.api_get_raw_data_table, name='api_get_raw_data_table'),
]