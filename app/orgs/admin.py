import autocomplete_all as admin
from admin_auto_filters.filters import AutocompleteFilter
from autocomplete_all import TabularInline
from django.db.models import Q

from app.mixins import AdminAjaxMixin
from app_auth.models import User
from orgs.models import Organisation, Contract


class OrgAdminFilter(AutocompleteFilter):
    field_name = 'organization'
    title = 'Организация'


class UserInline(TabularInline):
    model = User
    extra = 0
    classes = ['collapse']
    fields = 'username', 'last_name', 'first_name', 'second_name', 'main_manager'
    autocomplete_fields = 'main_manager',
    show_change_link = True


class ExpeditorUserInline(UserInline):
    fields = 'username', 'last_name', 'first_name', 'second_name'
    autocomplete_fields = None


class ContractInline(TabularInline):
    model = Contract
    extra = 0
    classes = ['collapse']


@admin.register(Organisation)
class OrgAdmin(admin.ModelAdmin, AdminAjaxMixin):
    list_display = '__str__', 'legal_name', 'inn', 'kpp', 'is_client'
    list_filter = 'is_client', 'is_expeditor'
    search_fields = 'name', 'legal_name', 'inn', 'kpp', 'ogrn'
    readonly_fields = 'is_expeditor',
    inlines = UserInline, ContractInline

    def get_inlines(self, request, obj):
        if obj is not None:
            if obj.is_expeditor:
                return ExpeditorUserInline,
            elif not obj.is_client:
                return tuple()
        return super(OrgAdmin, self).get_inlines(request, obj)

    def get_search_results_ajax(self, queryset, referer: str, key: str, urlparams: dict):

        if referer.startswith('app_auth/user/'):
            if referer.endswith('add/') or referer == 'app_auth/user/':
                return queryset.exclude(is_expeditor=False, is_client=False)
            elif referer.endswith('change/'):
                if self.check_multiple_bools(urlparams, 'is_staff', 'is_superuser'):
                    return queryset.filter(is_expeditor=True)
                return queryset.filter(is_client=True)
        elif referer.startswith('logistics/order/'):
            if 'client' in key:
                return queryset.filter(is_client=True)
        elif referer.startswith('orgs/contract/'):
            return queryset.exclude(Q(is_expeditor=True) | Q(is_expeditor=False, is_client=False))

        return queryset


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin, AdminAjaxMixin):
    search_fields = 'number',
    list_display = '__str__', 'organization', 'is_active'
    list_filter = OrgAdminFilter,

    def get_queryset(self, request):
        queryset = super(ContractAdmin, self).get_queryset(request)
        return queryset.select_related('organization')

    def get_search_results_ajax(self, queryset, referer: str, key: str, urlparams: dict):
        if referer.startswith('logistics/order/'):
            client_id = self.get_ajax_value(urlparams, 'client')
            return queryset.filter(organization_id=client_id)
        return queryset
