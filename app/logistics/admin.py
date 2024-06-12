import uuid

import autocomplete_all as admin
from django.contrib.admin import DateFieldListFilter, TabularInline, action, SimpleListFilter
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.widgets import AutocompleteSelect, RelatedFieldWidgetWrapper, \
    AdminFileWidget as BaseAdminFileWidget
from django.db import models
from django.db.models import OuterRef, Subquery, ForeignKey, ManyToManyField, Exists
from django.forms import TextInput, Textarea, NumberInput, ModelForm
from django import forms
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder
from admin_auto_filters.filters import AutocompleteFilter

from app.models import AbstractModel
from cats.models import Package
from docs.generators import XLSGenerator
from logistics.models import Order, Cargo, OrderStatus, AttachedDocument, ORDER_STATUS_LABELS, QuickAttachedDocument, \
    QuickOrder


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
    verbose_name_plural = 'Прошлые статусы заявки'


class AdminFileWidget(BaseAdminFileWidget):
    template_name = 'logistics/widgets/clearable_file_input.html'


class DocsInline(admin.TabularInline):
    model = AttachedDocument
    extra = 0
    classes = ['collapse']
    formfield_overrides = {models.FileField: {"widget": AdminFileWidget}}


class QuickDocsInline(admin.TabularInline):
    model = QuickAttachedDocument
    extra = 0
    min_num = 1
    formfield_overrides = {models.FileField: {"widget": AdminFileWidget}}
    readonly_fields = 'link',
    exclude = 'title', 'file'

    @staticmethod
    def link(obj):
        return format_html("<a download href='{url}'>{title}</a>", url=obj.file.url, title=obj.title)


class ClientFilter(AutocompleteFilter):
    field_name = 'client'
    title = 'Заказчик'


class ManagerFilter(AutocompleteFilter):
    field_name = 'manager'
    title = 'Менеджер'


class ClientEmployeeFilter(AutocompleteFilter):
    field_name = 'client_employee'
    title = 'Сотрудник заказчика'


class CreatedByFilter(AutocompleteFilter):
    field_name = 'created_by'
    title = 'Создатель быстрой заявки'


class ProcessedFilter(SimpleListFilter):
    parameter_name = 'processed'
    title = 'Заявка обработана'

    def lookups(self, request, model_admin):
        return ('true', 'Да'), ('false', 'Нет')

    def queryset(self, request, queryset):
        val = self.value()
        if val is not None:
            orders = Order.objects.filter(quick_order=OuterRef('pk'))
            queryset = queryset.annotate(processed=Exists(orders)).filter(processed=val.capitalize())
        return queryset


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
            ('status', 'status_updated'),
            ('client_number', 'gov_contract_number'),
            'service_marks',
            ('tracking_url', 'quick_order')
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
    readonly_fields = 'sum_weight', 'sum_volume', 'sum_quantity', 'status_updated'
    inlines = CargoInline, OrderStatusInline, DocsInline
    list_display = ('number', 'date', 'client_number', 'client', 'from_address_short', 'to_address_short',
                    'status', 'full_price',)
    list_filter = ClientFilter, ManagerFilter, ClientEmployeeFilter, ('date', DateRangeFilterBuilder()), StatusFilter
    old_state = None
    change_form_template = 'admin/order_change.html'
    tech_fields = '_state', 'id', 'created_at', 'last_update'
    exclude_from_copy_fields = 'number', 'client_number', 'date', 'status'
    actions = 'download_excel',
    act_on_filtered = 'download_excel',

    def get_fields_list(self, model=None, exclude=None):
        if model is None:
            model = self.model
        if exclude is None:
            exclude = []
        return [i for i in model._meta._forward_fields_map if not i.endswith('id') and i not in exclude]

    def get_related_fields_list(self, model=None, exclude=None):
        if model is None:
            model = self.model
        if exclude is None:
            exclude = []
        return [
            key for key, value in model._meta._forward_fields_map.items() if
            key not in exclude and not key.endswith('id') and isinstance(value, ForeignKey)
        ]

    def get_m2m_fields_list(self, model=None, exclude=None):
        if model is None:
            model = self.model
        if exclude is None:
            exclude = []
        return [
            key for key, value in model._meta._forward_fields_map.items() if
            key not in exclude and not key.endswith('id') and isinstance(value, ManyToManyField)
        ]

    @action(description="Выгрузить в Excel")
    def download_excel(self, request, queryset):
        if not queryset:
            if request.GET:
                queryset = queryset.model.objects.filter(**request.GET.dict())
            else:
                queryset = queryset.model.objects.all()
        generator = XLSGenerator(self.model, self.get_fields_list())
        response = generator.response(
            queryset.select_related(*self.get_related_fields_list()).prefetch_related(*self.get_m2m_fields_list())
        )
        return response

    def get_queryset(self, request):
        queryset = super(OrderAdmin, self).get_queryset(request)
        return queryset.prefetch_related('orderstatus_set').select_related(
            'client', 'client_employee', 'manager',
            'from_country', 'from_city', 'to_country', 'to_city'
        )

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        self.old_state = obj.get_state(related_objects='cargos')
        return obj

    def save_related(self, request, form, formsets, change):
        super(OrderAdmin, self).save_related(request, form, formsets, change)
        new_state = form.instance.get_state(related_objects='cargos')
        if self.old_state is None:
            form.instance.object_created(request, new_state)
        else:
            form.instance.object_updated(request, self.old_state, new_state)

    def add_view(self, request, form_url="", extra_context=None):
        self.old_state = None
        return super(OrderAdmin, self).add_view(request, form_url, extra_context)

    def copy_object(self, obj):
        obj_dict = obj.__dict__
        for field in obj._meta.many_to_many:
            obj_dict[field.name] = list(obj.__getattribute__(field.name).all())

        for field in self.tech_fields + self.exclude_from_copy_fields:
            obj_dict.pop(field)

        for key in list(obj_dict.keys()):
            if key.endswith('_id'):
                new_key = key[:-3]
                obj_dict[new_key] = obj_dict.pop(key)

        return obj_dict

    def get_changeform_initial_data(self, request):
        copy_order_pk = request.GET.get('copy_order')
        if copy_order_pk:
            copy_order = self.model.objects.get(pk=copy_order_pk)
            return self.copy_object(copy_order)

        data = super(OrderAdmin, self).get_changeform_initial_data(request)
        data['manager'] = request.user
        return data

    def changelist_view(self, request, extra_context=None):
        if request.POST.get('action', '') in self.act_on_filtered:
            if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                post.setlist(ACTION_CHECKBOX_NAME, [uuid.uuid4()])
                request._set_post(post)
        return super(OrderAdmin, self).changelist_view(request, extra_context)


@admin.register(QuickOrder)
class QuickOrderAdmin(admin.ModelAdmin):
    list_display = 'number', 'client_number', 'created_by', 'processed'
    list_filter = ClientFilter, CreatedByFilter, ProcessedFilter
    search_fields = 'number', 'client_number'
    readonly_fields = 'created_by', 'client', 'processed'
    inlines = QuickDocsInline,

    def get_queryset(self, request):
        queryset = super(QuickOrderAdmin, self).get_queryset(request)
        orders = Order.objects.filter(quick_order=OuterRef('pk'))
        return queryset.annotate(processed=Exists(orders))

    def processed(self, obj):
        return obj.processed

    processed.short_description = 'Обработана'
    processed.boolean = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
