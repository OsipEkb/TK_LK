# dashboard/urls.py
from django.urls import path
from . import views
from .api_views import DashboardDataAPI, VehicleDetailAPI

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vehicles/', views.vehicles_page, name='vehicles'),
    path('reports/', views.reports, name='reports'),
    path('retransmission/', views.retransmission, name='retransmission'),
    path('billing/', views.billing, name='billing'),
    path('support/', views.support, name='support'),

    # API endpoints
    path('api/data/', DashboardDataAPI.as_view(), name='dashboard_api'),
    path('api/vehicle/<str:vehicle_id>/', VehicleDetailAPI.as_view(), name='vehicle_detail_api'),

    # Временный debug
    path('test-apis/', views.test_all_properties_apis, name='test_apis'),
    path('test-enhanced/', views.test_enhanced_dashboard, name='test_enhanced'),
    path('test-online-apis/', views.test_online_apis, name='test_online_apis'),
    path('test-parsing/', views.test_parsing, name='test_parsing'),
    path('test-final/', views.test_final_dashboard, name='test_final'),
    path('test-fuel/', views.test_fuel_sources, name='test_fuel'),
    path('test-final-fuel/', views.test_final_fuel, name='test_final_fuel'),
    path('debug-fuel-parsing/', views.debug_fuel_parsing, name='debug_fuel_parsing'),
    path('test-final-with-fuel/', views.test_final_with_fuel, name='test_final_with_fuel'),
    path('debug-raw-data/', views.debug_raw_data, name='debug_raw_data'),
]