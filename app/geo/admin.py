import re

import autocomplete_all as admin
# from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter
from autocomplete_all import TabularInline

from app.mixins import AdminAjaxMixin
from geo.models import Country, City


class CountryFilter(AutocompleteFilter):
    field_name = 'country'
    title = 'Страна'

    def lookups(self, request, model_admin):
        return tuple()


class CityInline(TabularInline):
    model = City
    autocomplete_all = False
    extra = 0
    classes = ['collapse']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    search_fields = 'name',
    inlines = CityInline,


@admin.register(City)
class CityAdmin(admin.ModelAdmin, AdminAjaxMixin):
    search_fields = 'name',
    list_display = '__str__', 'country'
    list_filter = CountryFilter,

    def get_queryset(self, request):
        queryset = super(CityAdmin, self).get_queryset(request)
        return queryset

    @staticmethod
    def get_country_field(key, default='country'):
        match = re.search(r'id_(?P<prefix>[a-z]*)_?city', key)
        if match:
            prefix = match.groupdict().get('prefix')
            if prefix:
                return f'{prefix}_{default}'
        return default

    def get_search_results_ajax(self, queryset, referer: str, key: str, urlparams: dict):
        if referer.startswith('logistics/order/'):
            if key.endswith('city'):
                country_id = self.get_ajax_value(urlparams, self.get_country_field(key))
                return queryset.filter(country_id=country_id)
        return queryset
