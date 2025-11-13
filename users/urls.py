from django.urls import path
from . import views, views_api

app_name = 'users'  # ДОБАВЬ ЭТУ СТРОКУ

urlpatterns = [
    # HTML routes
    path('login/', views.HTMLLoginView.as_view(), name='login'),
    path('logout/', views.html_logout, name='logout'),

    # API routes
    path('api/login/', views.autograph_login, name='api_login'),
    path('api/logout/', views.custom_logout, name='api_logout'),
    path('api/profile/', views.user_profile, name='api_profile'),
    path('api/health/', views.health_check, name='api_health'),

    # Legacy API routes
    path('api/auth/login/', views_api.login_view, name='auth_login'),
    path('api/auth/logout/', views_api.logout_view, name='auth_logout'),
    path('api/auth/profile/', views_api.user_profile, name='auth_profile'),
]