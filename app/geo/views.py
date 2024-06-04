from django.shortcuts import render
from django.views.generic import CreateView

from geo.models import Country, City
from orgs.views import PopUpMixin


class CountryAddView(PopUpMixin, CreateView):
    model = Country
    template_name = 'geo/country_add.html'
    fields = '__all__'


class CityAddView(PopUpMixin, CreateView):
    model = City
    template_name = 'geo/city_add.html'
    fields = '__all__'
