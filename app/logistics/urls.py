from django.urls import path
from django_filters.views import FilterView

from logistics.filtersets import OrderFilterSet
from logistics.views import OrderDetailView, OrderStatusView, OrderCreateView, OrderUpdateView, OrderListView

urlpatterns = [
    path('list', OrderListView.as_view(), name='orders_list'),
    path('create', OrderCreateView.as_view(), name='order_create'),
    path('<uuid:pk>', OrderDetailView.as_view(), name='order_detail'),
    path('<uuid:pk>/update', OrderUpdateView.as_view(), name='order_update'),
    path('<uuid:pk>/status', OrderStatusView.as_view(), name='order_status'),
]
