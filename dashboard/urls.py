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

]