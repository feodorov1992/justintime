from django.urls import path

from geo.views import CountryAddView, CityAddView

urlpatterns = [
    path('country/add/', CountryAddView.as_view(), name='country_add'),
    path('city/add/', CityAddView.as_view(), name='city_add'),
]
