import autocomplete_all as admin

from logistics.models import Order, Cargo


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = 'number', 'client_number', 'gov_contract_number'


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    search_fields = 'mark',
