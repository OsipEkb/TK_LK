# vehicles/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicles_main, name='vehicles_main'),

    # API endpoints
    path('api/get-vehicles/', views.api_get_vehicles, name='api_get_vehicles'),
    path('api/get-historical-data/', views.api_get_historical_data, name='api_get_historical_data'),
    path('api/get-parameter-groups/', views.api_get_parameter_groups, name='api_get_parameter_groups'),
]