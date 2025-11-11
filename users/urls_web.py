from django.urls import path
from django.contrib.auth import views as auth_views
from . import views_web

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views_web.SignUpView.as_view(), name='signup'),
    path('profile/', views_web.ProfileView.as_view(), name='profile'),
]