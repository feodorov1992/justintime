import autocomplete_all as admin

from cats.models import Currency, Service, Package, CargoParam


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    search_fields = 'code', 'name'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    search_fields = 'name',


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    search_fields = 'name',


@admin.register(CargoParam)
class CargoParamAdmin(admin.ModelAdmin):
    search_fields = 'name',
