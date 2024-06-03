from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.shortcuts import render
from django.urls import reverse


class LoginView(BaseLoginView):
    template_name = 'app_auth/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('admin:index')
        return reverse('orders_list')


class LogoutView(BaseLogoutView):

    def get_success_url(self):
        return reverse('login')
