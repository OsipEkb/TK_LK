from django.shortcuts import render
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import User


class SignUpView(CreateView):
    model = User
    template_name = 'users/signup.html'
    fields = ['username', 'email', 'password', 'first_name', 'last_name']
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'users/profile.html'
    fields = ['first_name', 'last_name', 'email', 'phone']
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user