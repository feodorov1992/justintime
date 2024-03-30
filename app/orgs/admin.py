import autocomplete_all as admin

from orgs.models import Organisation, Contract


@admin.register(Organisation)
class OrgAdmin(admin.ModelAdmin):
    list_display = '__str__', 'is_client', 'is_expeditor'
    list_filter = 'is_client', 'is_expeditor'
    search_fields = 'inn', 'kpp', 'ogrn', 'name', 'legal_name'
    readonly_fields = 'is_expeditor',

    def get_search_results_ajax(self, queryset, referer, key, urlparams):

        if referer.startswith('app_auth/user/'):
            if referer == 'app_auth/user/add/':
                return queryset.exclude(is_expeditor=False, is_client=False)

            is_staff = urlparams.get('is_staff', ['false'])
            is_staff = True if is_staff == ['true'] else False
            is_superuser = urlparams.get('is_superuser', ['false'])
            is_superuser = True if is_superuser == ['true'] else False

            if key == 'id_organization':
                if is_staff or is_superuser:
                    return queryset.filter(is_expeditor=True)
                return queryset.filter(is_client=True)

        return queryset


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    search_fields = 'number',
    list_display = '__str__', 'organization', 'is_active'
    list_filter = 'organization',

    def get_queryset(self, request):
        queryset = super(ContractAdmin, self).get_queryset(request)
        return queryset.select_related('organization')
