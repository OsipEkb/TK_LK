from django.urls import path
from . import views, api_views

app_name = 'reports'

urlpatterns = [
    # Страницы
    path('', views.reports_page, name='reports_page'),

    # API endpoints
    path('api/vehicles/list/', api_views.ReportsVehicleListAPI.as_view(), name='reports_vehicles_list'),
    path('api/generate/', api_views.GenerateReportAPI.as_view(), name='generate_report'),
]