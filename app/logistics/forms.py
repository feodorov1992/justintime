from django import forms
from django.forms import ModelForm, inlineformset_factory

from logistics.filtersets import ClientWidget, MySelect2Widget
from logistics.models import Order, Cargo, QuickOrder, QuickAttachedDocument


class ContractWidget(MySelect2Widget):
    search_field_names = 'number',
    dependent_fields = {'client': 'organization'}

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        if not request.user.is_staff:
            dependent_fields['organization'] = request.user.organization.id
        elif not dependent_fields:
            dependent_fields['organization'] = None
        return super(ContractWidget, self).filter_queryset(request, term, queryset, **dependent_fields)


class CountryWidget(MySelect2Widget):
    search_field_names = 'name',


class CityWidget(MySelect2Widget):
    search_field_names = 'name',

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        if not dependent_fields and self.dependent_fields:
            dependent_fields = {key: None for key in self.dependent_fields.values()}
        return super().filter_queryset(request, term, queryset, **dependent_fields)


class FromCityWidget(CityWidget):
    dependent_fields = {'from_country': 'country'}


class ToCityWidget(CityWidget):
    dependent_fields = {'to_country': 'country'}


class CounterpartyWidget(MySelect2Widget):
    search_field_names = 'name',


class PackageWidget(MySelect2Widget):
    search_field_names = 'name',


class OrderForm(ModelForm):
    required_css_class = 'required'

    from_index = forms.CharField(label='Индекс', widget=forms.NumberInput)
    to_index = forms.CharField(label='Индекс', widget=forms.NumberInput)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(OrderForm, self).__init__(*args, **kwargs)
        if user is not None and not user.is_staff:
            del self.fields['client']
        self.label_suffix = None
        for field_name in self.fields:
            if 'currency' in field_name:
                self.fields[field_name].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return obj.displayed_name

    def as_my_style(self):
        context = super().get_context()
        context['fields'] = {f_e[0].name: f_e[0] for f_e in context['fields']}
        context['hidden_fields'] = {f_e.name: f_e for f_e in context['hidden_fields']}
        return self.render('logistics/forms/order.html', context=context)

    class Meta:
        model = Order
        fields = ('client_number', 'date', 'client', 'contract', 'cargo_name', 'cargo_value', 'cargo_value_currency',
                  'insurance_needed', 'cargo_origin', 'gov_contract_number', 'services', 'comment', 'from_org',
                  'from_date_wanted', 'from_contacts', 'from_index', 'from_country', 'from_city', 'from_address',
                  'from_label', 'to_org', 'to_date_wanted', 'to_contacts', 'to_index', 'to_country', 'to_city',
                  'to_address', 'to_label')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'services': forms.CheckboxSelectMultiple(attrs={'class': 'checkboxes'}),
            'client': ClientWidget,
            'contract': ContractWidget,
            'cargo_origin': CountryWidget,
            'from_org': CounterpartyWidget,
            'from_date_wanted': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'from_country': CountryWidget,
            'from_city': FromCityWidget,
            'to_org': CounterpartyWidget,
            'to_date_wanted': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'to_country': CountryWidget,
            'to_city': ToCityWidget,
        }


class CargoForm(ModelForm):
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super(CargoForm, self).__init__(*args, **kwargs)
        self.label_suffix = None

    def as_my_style(self):
        context = super().get_context()
        context['fields'] = {f_e[0].name: f_e[0] for f_e in context['fields']}
        context['hidden_fields'] = {f_e.name: f_e for f_e in context['hidden_fields']}
        return self.render('logistics/forms/cargo.html', context=context)

    class Meta:
        model = Cargo
        fields = '__all__'
        widgets = {
            'params': forms.CheckboxSelectMultiple(attrs={'class': 'checkboxes'}),
            'package': PackageWidget
        }


CargoFormset = inlineformset_factory(Order, Cargo, form=CargoForm, extra=0, min_num=1, validate_min=True)


class QuickOrderForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        fields = 'client_number',
        model = QuickOrder


class QuickDocForm(ModelForm):
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super(QuickDocForm, self).__init__(*args, **kwargs)
        self.label_suffix = None

    def as_my_style(self):
        context = super().get_context()
        context['fields'] = {f_e[0].name: f_e[0] for f_e in context['fields']}
        context['hidden_fields'] = {f_e.name: f_e for f_e in context['hidden_fields']}
        return self.render('logistics/forms/quick_order_file.html', context=context)

    class Meta:
        model = QuickAttachedDocument
        fields = 'title', 'file'


QuickDocFormset = inlineformset_factory(QuickOrder, QuickAttachedDocument, form=QuickDocForm,
                                        extra=0, min_num=1, validate_min=True)
