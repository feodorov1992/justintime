from django.shortcuts import render
from django_filters import FilterSet
from django_filters.views import FilterView
from django_genericfilters.views import FilteredListView

from logistics.forms import OrderListFilters
from logistics.models import Order
