# vehicles/urls.py
from django.urls import path
from .views_enhanced import (
    VehicleListAPI,
    EnhancedAnalyticsAPI,
    VehicleStatisticsAPI,
    VehicleOnlineStatusAPI,
    SystemHealthAPI
)

urlpatterns = [
    path('api/vehicles/page-list/', VehicleListAPI.as_view(), name='vehicle-list'),
    path('api/enhanced-analytics/', EnhancedAnalyticsAPI.as_view(), name='enhanced-analytics'),
    path('api/vehicle-statistics/', VehicleStatisticsAPI.as_view(), name='vehicle-statistics'),
    path('api/vehicle-online-status/', VehicleOnlineStatusAPI.as_view(), name='vehicle-online-status'),
    path('api/system-health/', SystemHealthAPI.as_view(), name='system-health'),
]