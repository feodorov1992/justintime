from django import forms
from django_genericfilters import forms as gf
from django_select2.forms import ModelSelect2Widget

from app_auth.models import User
from logistics.models import ORDER_STATUS_LABELS
from orgs.models import Organisation


class ClientWidget(ModelSelect2Widget):
    search_field_names = 'name', 'legal_name', 'inn', 'kpp', 'ogrn'
    search_fields = {f'{field_name}__icontains' for field_name in search_field_names}

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        return super(ClientWidget, self).filter_queryset(request, term, queryset, **dependent_fields)

    def get_queryset(self):
        qs = super(ClientWidget, self).get_queryset()
        return qs.filter(is_client=True)


class ManagerWidget(ModelSelect2Widget):
    search_field_names = 'username', 'first_name', 'last_name', 'email'
    search_fields = {f'{field_name}__icontains' for field_name in search_field_names}

    def get_queryset(self):
        qs = super(ManagerWidget, self).get_queryset()
        return qs.filter(organization__is_expeditor=True).select_related('organization')


class OrderListFilters(gf.FilteredForm):
    query = forms.CharField(label='Поиск', required=False)

    status = gf.ChoiceField(choices=ORDER_STATUS_LABELS, label='Статус', required=False)
    client = forms.ModelChoiceField(label='Заказчик', required=False, empty_label=None,
                                    queryset=Organisation.objects.all(), widget=ClientWidget)
    manager = forms.ModelChoiceField(queryset=User.objects.all(),
                                     label='Менеджер', required=False, empty_label=None, widget=ManagerWidget)
    date__gte = forms.DateField(label='Не ранее', required=False, widget=forms.DateInput(attrs={'type': 'date'},
                                                                                         format='%Y-%m-%d'))
    date__lte = forms.DateField(label='Не позднее', required=False, widget=forms.DateInput(attrs={'type': 'date'},
                                                                                           format='%Y-%m-%d'))

    def get_order_by_choices(self):
        return list()
