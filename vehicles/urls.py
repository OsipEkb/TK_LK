# vehicles/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # Страницы
    path('', views.vehicles_page, name='vehicles'),
    path('dashboard/<str:vehicle_id>/', views.vehicle_dashboard, name='vehicle_dashboard'),
    path('charts/', views.vehicle_charts, name='vehicle_charts'),
    path('analytics/', views.analytics_page, name='vehicle_analytics'),
    path('statistics/', views.statistics_page, name='vehicle_statistics'),
    path('api-test/', views.api_test_page, name='vehicle_api_test'),
    path('debug/', views.debug_dashboard, name='vehicle_debug'),
    path('data-collection/', views.data_collection_page, name='data_collection'),
    path('debug-historical/', views.debug_historical, name='vehicles-debug-historical'),

    # API endpoints
    path('api/vehicles/', api_views.VehicleListAPI.as_view(), name='vehicles-list'),
    path('api/vehicles/sync/', api_views.VehicleSyncAPI.as_view(), name='vehicles-sync'),
    path('api/vehicles/page-list/', api_views.VehicleListForPageAPI.as_view(), name='vehicles-page-list'),
    path('api/vehicles/statistics/', api_views.VehicleStatisticsAPI.as_view(), name='vehicles-statistics'),
    path('api/vehicles/<str:vehicle_id>/historical/', api_views.VehicleHistoricalDataAPI.as_view(),
         name='vehicle-historical'),
    path('api/vehicles/online/', api_views.VehicleOnlineDataAPI.as_view(), name='vehicles-online'),
    path('api/debug/', api_views.VehicleDebugAPI.as_view(), name='vehicles-debug'),
    path('api/data-collection/', api_views.DataCollectionAPI.as_view(), name='vehicles-data-collection'),
    path('api/debug-historical/', api_views.VehicleHistoricalDebugAPI.as_view(), name='vehicles-debug-historical'),
]