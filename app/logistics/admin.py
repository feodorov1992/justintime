import autocomplete_all as admin
from django.contrib.admin import DateFieldListFilter, TabularInline
from django.contrib.admin.widgets import AutocompleteSelect, RelatedFieldWidgetWrapper
from django.db import models
from django.db.models import OuterRef, Subquery
from django.forms import TextInput, Textarea, NumberInput, ModelForm
from django import forms
from rangefilter.filters import DateRangeFilterBuilder
from admin_auto_filters.filters import AutocompleteFilter

from cats.models import Package
from logistics.models import Order, Cargo, OrderStatus, AttachedDocument, ORDER_STATUS_LABELS


class CargoInline(admin.TabularInline):
    model = Cargo
    extra = 0
    classes = ['collapse']
    min_num = 1

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.FloatField: {'widget': NumberInput(attrs={'style': 'width: 60px'})},
        models.IntegerField: {'widget': NumberInput(attrs={'style': 'width: 60px'})}
    }

    def get_queryset(self, request):
        queryset = super(CargoInline, self).get_queryset(request)
        return queryset.select_related('package').prefetch_related('params')


class AlwaysChangedModelForm(ModelForm):
    def has_changed(self):
        return True


class OrderStatusInline(admin.TabularInline):
    model = OrderStatus
    extra = 0
    classes = ['collapse']
    form = AlwaysChangedModelForm


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


class ClientEmployeeFilter(AutocompleteFilter):
    field_name = 'client_employee'
    title = 'Сотрудник заказчика'


class StatusFilter(admin.SimpleListFilter):
    title = 'Статус'
    parameter_name = 'status'

    def queryset(self, request, queryset):
        status_name = request.GET.get(self.parameter_name)
        if status_name is not None:
            statuses = OrderStatus.objects.filter(order=OuterRef('pk'))
            return queryset.annotate(status=Subquery(statuses.values('name')[:1])).filter(status=status_name)
        return queryset

    def lookups(self, request, model_admin):
        return ORDER_STATUS_LABELS


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
                    'status_short', 'full_price',)
    list_filter = ClientFilter, ManagerFilter, ClientEmployeeFilter, ('date', DateRangeFilterBuilder()), StatusFilter
    old_state = None

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        return queryset.prefetch_related('orderstatus_set').select_related(
            'client', 'client_employee', 'manager',
            # 'cargo_origin', 'cargo_value_currency', 'insurance_beneficiary', 'price_currency',
            'from_country', 'from_city', 'to_country', 'to_city'
        )

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        self.old_state = obj.get_state(related_objects='cargos')
        return obj

    def save_model(self, request, obj, form, change):
        super(OrderAdmin, self).save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super(OrderAdmin, self).save_related(request, form, formsets, change)
        new_state = form.instance.get_state(related_objects='cargos')
        print(self.old_state)
        print(new_state)
        print(form.instance.get_state_changes(self.old_state, new_state))

    def save_formset(self, request, form, formset, change):
        super(OrderAdmin, self).save_formset(request, form, formset, change)
        # if formset.model is Cargo:
        #     print(f'{formset.model.__name__} formset is being saved!')
        #     formset.instance.sum_cargo_params(commit=True)
