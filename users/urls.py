# users/urls.py
from django.urls import path
from .views import LoginView, logout_view, check_session, session_info

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('check-session/', check_session, name='check_session'),
    path('session-info/', session_info, name='session_info'),
]