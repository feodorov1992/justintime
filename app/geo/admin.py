import autocomplete_all as admin

from geo.models import Country, City


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    search_fields = 'name',


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    search_fields = 'name',
