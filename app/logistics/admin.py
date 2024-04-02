import autocomplete_all as admin
from django.contrib.admin import DateFieldListFilter, TabularInline
from django.contrib.admin.widgets import AutocompleteSelect, RelatedFieldWidgetWrapper
from django.db import models
from django.forms import TextInput, Textarea, NumberInput
from django import forms
from rangefilter.filters import DateRangeFilterBuilder
from admin_auto_filters.filters import AutocompleteFilter

from cats.models import Package
from logistics.models import Order, Cargo, OrderStatus, AttachedDocument


class CargoInline(admin.TabularInline):
    model = Cargo
    extra = 0
    classes = ['collapse']

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.FloatField: {'widget': NumberInput(attrs={'style': 'width: 60px'})},
        models.IntegerField: {'widget': NumberInput(attrs={'style': 'width: 60px'})}
    }

    def get_queryset(self, request):
        queryset = super(CargoInline, self).get_queryset(request)
        return queryset.select_related('package').prefetch_related('params')


class OrderStatusInline(admin.TabularInline):
    model = OrderStatus
    extra = 0
    classes = ['collapse']


class DocsInline(admin.TabularInline):
    model = AttachedDocument
    extra = 0
    classes = ['collapse']


class ClientFilter(AutocompleteFilter):
    field_name = 'client'
    title = 'Заказчик'


class ManagerFilter(AutocompleteFilter):
    field_name = 'manager'
    title = 'Менеджер'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = 'number', 'client_number', 'gov_contract_number'
    fieldsets = (
        (None, {'fields': (
            ('number', 'date'),
            'status',
            ('client_number', 'gov_contract_number'),
            'service_marks', 'tracking_url'
        )}),
        ('Взаимодействие с заказчиком', {'fields': (
            ('client', 'client_employee'),
            ('contract', 'manager'),
            ('services', 'comment')
        )}),
        ('Отправление', {'fields': (
            ('from_org', 'from_label'),
            ('from_index', 'from_country', 'from_city'),
            'from_address',
            'from_contacts',
        )}),
        ('Доставка', {'fields': (
            ('to_org', 'to_label'),
            ('to_index', 'to_country', 'to_city'),
            'to_address',
            'to_contacts',
        )}),
        ('Контрольные даты', {'fields': (
            ('from_date_wanted', 'to_date_wanted'),
            ('from_date_plan', 'to_date_plan'),
            ('from_date_fact', 'to_date_fact')
        )}),
        ('Информация о грузе', {'fields': (
            ('cargo_name', 'cargo_origin'),
            ('sum_weight', 'sum_volume', 'sum_quantity'),
        )}),
        ('Информация для расчетов', {'fields': (
            ('price', 'price_currency'),
            ('insurance_needed', 'cargo_value', 'cargo_value_currency'),
            ('insurance_premium', 'insurance_sum_rate', 'insurance_beneficiary'),
        )})
    )
    readonly_fields = 'sum_weight', 'sum_volume', 'sum_quantity', 'status'
    inlines = CargoInline, OrderStatusInline, DocsInline
    list_display = ('number', 'date', 'client_number', 'client', 'from_address_short', 'to_address_short',
                    'from_address_full', 'to_address_full',)
    list_filter = ClientFilter, ManagerFilter, ('date', DateRangeFilterBuilder()),

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        return queryset.prefetch_related('orderstatus_set').select_related(
            'client', 'client_employee', 'manager',
            # 'cargo_origin', 'cargo_value_currency', 'insurance_beneficiary', 'price_currency',
            'from_country', 'from_city', 'to_country', 'to_city'
        )

    def save_formset(self, request, form, formset, change):
        super(OrderAdmin, self).save_formset(request, form, formset, change)
        formset.instance.sum_cargo_params(commit=True)
