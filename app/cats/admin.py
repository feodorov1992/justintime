# from django.contrib import admin
import autocomplete_all as admin

from cats.models import Organisation


@admin.register(Organisation)
class OrgAdmin(admin.ModelAdmin):
    list_display = '__str__', 'is_client', 'is_expeditor'
    search_fields = 'inn', 'kpp', 'ogrn', 'name', 'legal_name'
    readonly_fields = 'is_expeditor',

    def get_search_results_ajax(self, queryset, referer, key, urlparams):

        if referer.startswith('app_auth/user/'):
            is_staff = urlparams.get('is_staff', ['false'])
            is_staff = True if is_staff == ['true'] else False
            is_superuser = urlparams.get('is_superuser', ['false'])
            is_superuser = True if is_superuser == ['true'] else False

            if key == 'id_organization':
                if is_staff or is_superuser:
                    return queryset.filter(is_expeditor=True)
                return queryset.filter(is_expeditor=False)

        return queryset
