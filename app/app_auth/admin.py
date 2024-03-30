import autocomplete_all as admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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

    @staticmethod
    def get_ajax_value(source, key, default=None):
        value = source.get(key, default)
        if value and isinstance(value, list):
            return value[0]
        return value

    def get_ajax_bool(self, source, key):
        positives = 'true', 'on', 'yes', 'y', '1'
        value = self.get_ajax_value(source, key, False)
        return str(value).lower() in positives

    def get_search_results_ajax(self, queryset, referer, key, urlparams):
        if referer.startswith('app_auth/user/'):
            if key == 'id_main_manager':
                is_staff = self.get_ajax_bool(urlparams, 'is_staff')
                is_superuser = self.get_ajax_bool(urlparams, 'is_superuser')
                if is_staff or is_superuser:
                    return queryset.none()
                username = self.get_ajax_value(urlparams, 'username')
                queryset = queryset.filter(organization__is_expeditor=True)
                sub_qs = queryset.filter(username=username)
                if sub_qs.exists():
                    return queryset.exclude(id=sub_qs.first().id)
        return queryset


admin.site.unregister(DjangoGroup)
