from django.forms import ModelForm

from geo.models import Country, City
from logistics.filtersets import MySelect2Widget


class CountryWidget(MySelect2Widget):
    search_field_names = 'name',


class CountryForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Country
        fields = '__all__'


class CityForm(ModelForm):
    required_css_class = 'required'

    class Meta:
        model = City
        fields = '__all__'
        widgets = {'country': CountryWidget}
