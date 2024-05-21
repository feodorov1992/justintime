from django.contrib import messages
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import DetailView
from django_filters import FilterSet
from django_filters.views import FilterView
from django_genericfilters.views import FilteredListView

from logistics.forms import OrderListFilters
from logistics.models import Order


class OrderDetailView(DetailView):
    model = Order
    template_name = 'logistics/order_detail.html'


class OrderStatusView(DetailView):
    model = Order
    template_name = 'logistics/order_status.html'
