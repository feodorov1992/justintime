from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import render
from django.urls import reverse


class LoginView(BaseLoginView):
    template_name = 'app_auth/login.html'

    def get_success_url(self):
        return reverse('orders_list')
