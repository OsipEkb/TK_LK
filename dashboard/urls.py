# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vehicles/', views.vehicles_page, name='vehicles'),
    path('reports/', views.reports, name='reports'),
    path('retransmission/', views.retransmission, name='retransmission'),
    path('billing/', views.billing, name='billing'),
    path('support/', views.support, name='support'),

    # API endpoints
    path('api/data/', views.dashboard_api, name='dashboard_api'),
    path('api/vehicle/<str:vehicle_id>/', views.vehicle_detail_api, name='vehicle_detail_api'),
]