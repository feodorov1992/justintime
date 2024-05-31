import django_filters
from django import forms
from django.db import models
from django.db.models import Q
from django_select2.forms import ModelSelect2Widget

from app_auth.models import User
from logistics.models import Order, ORDER_STATUS_LABELS
from orgs.models import Organisation


class MySelect2Widget(ModelSelect2Widget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_fields = {f'{field_name}__icontains' for field_name in self.search_field_names}
        self.attrs = {
            "data-minimum-input-length": 0
        }


class ClientWidget(MySelect2Widget):
    search_field_names = 'name', 'legal_name', 'inn', 'kpp', 'ogrn'

    def get_queryset(self):
        qs = super(ClientWidget, self).get_queryset()
        return qs.filter(is_client=True)


class ManagerWidget(MySelect2Widget):
    search_field_names = 'username', 'first_name', 'last_name', 'email'

    def get_queryset(self):
        qs = super(ManagerWidget, self).get_queryset()
        return qs.filter(organization__is_expeditor=True).select_related('organization')


class OrderFilterSet(django_filters.FilterSet):
    client = django_filters.ModelChoiceFilter(widget=ClientWidget, queryset=Organisation.objects.all())
    manager = django_filters.ModelChoiceFilter(widget=ManagerWidget, queryset=User.objects.all())
    status = django_filters.MultipleChoiceFilter(widget=forms.CheckboxSelectMultiple,
                                                 choices=ORDER_STATUS_LABELS)
    date__gte = django_filters.DateFilter(widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'), field_name='date', lookup_expr='gte', label='Не ранее')
    date__lte = django_filters.DateFilter(widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'), field_name='date', lookup_expr='lte', label='Не позднее')
    search = django_filters.CharFilter(method='search_filter', label='Поиск по номеру')

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(number__icontains=value) | Q(client_number__icontains=value)
        )

    @property
    def qs(self):
        qs = super(OrderFilterSet, self).qs
        if not self.request.user.is_staff:
            return qs.filter(client=self.request.user.organization)
        return qs.select_related('price_currency')

    class Meta:
        model = Order
        fields = 'client', 'manager', 'status',
        # fields = {
        #     'client': ['exact'],
        #     'manager': ['exact'],
        #     'status': ['exact'],
        #     'date': ['gte', 'lte']
        # }
        filter_overrides = {
            models.DateField: {
                'filter_class': django_filters.DateFilter,
                'extra': lambda f: {
                    'widget': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                },
            },
        }
