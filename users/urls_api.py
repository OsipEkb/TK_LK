from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views_api

urlpatterns = [
    path('login/', views_api.login_view, name='api_login'),
    path('logout/', views_api.logout_view, name='api_logout'),
    path('profile/', views_api.user_profile, name='user_profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]