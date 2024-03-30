# from django.contrib import admin
import uuid

import autocomplete_all as admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.db.models import Q
from django.forms import ModelForm

from app_auth.models import Group, User, DjangoGroup


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


class UserCreationForm(ModelForm):

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'second_name', 'organization', 'main_manager')


@admin.register(User)
class UserAdmin(BaseUserAdmin, admin.ModelAdmin):
    list_display = '__str__', 'organization', 'email', 'is_staff'
    list_filter = 'is_staff', 'is_superuser', 'is_active', 'groups'
    search_fields = 'username', 'first_name', 'last_name', 'email'
    add_form = UserCreationForm
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'last_name', 'first_name', 'second_name', 'organization', 'main_manager'),
            },
        ),
    )
    ordering = 'last_name',
    readonly_fields = 'email',
    autocomplete_fields = 'organization', 'main_manager'
    fieldsets = (
        (None, {'fields': ('username', 'password', 'main_manager', 'organization')}),
        ('Персональная информация', {'fields': ('last_name', 'first_name', 'second_name', 'email')}),
        (
            'Права доступа',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    def get_search_results_ajax(self, queryset, referer, key, urlparams):
        if referer.startswith('app_auth/user/'):
            is_staff = urlparams.get('is_staff', ['false'])
            is_staff = True if is_staff == ['true'] else False
            is_superuser = urlparams.get('is_superuser', ['false'])
            is_superuser = True if is_superuser == ['true'] else False
            if key == 'id_main_manager':
                if is_staff or is_superuser:
                    return queryset.none()
                return queryset.filter(organization__is_expeditor=True)
        return queryset


admin.site.unregister(DjangoGroup)
