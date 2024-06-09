import autocomplete_all as admin
from django.contrib import messages
from django.contrib.admin import action
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import ModelForm
from django.shortcuts import redirect

from app.mixins import AdminAjaxMixin
from app_auth.models import Group, User, DjangoGroup
from app_auth.notifications import user_confirm, user_confirm_mass
from orgs.admin import OrgAdminFilter


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    pass


class UserCreationForm(ModelForm):

    class Meta:
        model = User
        fields = 'username', 'last_name', 'first_name', 'second_name', 'organization', 'main_manager'


@admin.register(User)
class UserAdmin(BaseUserAdmin, admin.ModelAdmin, AdminAjaxMixin):
    list_display = '__str__', 'organization', 'email', 'is_staff'
    list_filter = OrgAdminFilter, 'is_staff', 'is_superuser', 'is_active'
    search_fields = 'username', 'first_name', 'last_name', 'email'
    change_form_template = 'admin/user_change.html'
    add_form = UserCreationForm
    actions = 'send_confirm_emails', 'deactivate'
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

    def get_search_results_ajax(self, queryset, referer: str, key: str, urlparams: dict):
        if key and 'manager' in key:
            queryset = queryset.filter(organization__is_expeditor=True)
            if referer.startswith('app_auth/user/'):
                if self.check_multiple_bools(urlparams, 'is_staff', 'is_superuser'):
                    return queryset.none()
                username = self.get_ajax_value(urlparams, 'username')
                sub_qs = queryset.filter(username=username)
                if sub_qs.exists():
                    return queryset.exclude(id=sub_qs.first().id)
        elif key and 'client_employee' in key:
            client_id = self.get_ajax_value(urlparams, 'client') or self.get_ajax_value(urlparams, 'client__pk__exact')
            if client_id:
                return queryset.filter(organization_id=client_id)
            return queryset.none()
        return queryset

    @action(description="Отправить регистрационные письма")
    def send_confirm_emails(self, request, queryset):
        if not queryset:
            if request.GET:
                queryset = queryset.model.objects.filter(**request.GET.dict())
            else:
                queryset = queryset.model.objects.all()
        user_confirm_mass.delay(list(queryset.values_list('id', flat=True)))
        messages.success(request, 'Отправлено')
        return redirect(request.META.get('HTTP_REFERER'))

    @action(description="Деактивировать")
    def deactivate(self, request, queryset):
        if not queryset:
            if request.GET:
                queryset = queryset.model.objects.filter(**request.GET.dict())
            else:
                queryset = queryset.model.objects.all()
        queryset.update(is_active=False)
        messages.success(request, f'Пользователи деактивированы: {queryset.count()}')
        return redirect(request.META.get('HTTP_REFERER'))

admin.site.unregister(DjangoGroup)
