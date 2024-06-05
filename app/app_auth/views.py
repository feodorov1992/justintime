from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth.views import PasswordChangeView as BasePasswordChangeView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import UpdateView, CreateView

from app_auth.forms import UserForm, OrgForm
from app_auth.models import User


class ReturnBackMixin:

    def return_link(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse('home')


class LoginView(BaseLoginView):
    template_name = 'app_auth/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('admin:index')
        return reverse('orders_list')


class LogoutView(BaseLogoutView):

    def get_success_url(self):
        return reverse('login')


class UserAddView(LoginRequiredMixin, ReturnBackMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'app_auth/user_add.html'
    login_url = 'login'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        if self.request.user.is_staff:
            self.object.is_staff = True
        self.object.organization = self.request.user.organization
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, f'Пользователь {self.object} успешно добавлен')
        return self.return_link()


class UserEditView(LoginRequiredMixin, ReturnBackMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'app_auth/user_edit.html'
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'Ваш профиль успешно изменен')
        return self.return_link()


class OrgEditView(LoginRequiredMixin, ReturnBackMixin, UpdateView):
    model = User
    form_class = OrgForm
    template_name = 'app_auth/org_edit.html'
    login_url = 'login'

    def get_object(self, queryset=None):
        return self.request.user.organization

    def get_success_url(self):
        messages.success(self.request, f'Профиль организации {self.object.legal_name} успешно изменен')
        return self.return_link()


class PasswordChangeView(LoginRequiredMixin, ReturnBackMixin, BasePasswordChangeView):
    template_name = 'app_auth/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'Пароль успешно изменен')
        return self.return_link()
