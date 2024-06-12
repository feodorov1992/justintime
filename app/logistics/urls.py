from django.urls import path
from django_filters.views import FilterView

from logistics.filtersets import OrderFilterSet
from logistics.views import OrderDetailView, OrderStatusView, OrderCreateView, OrderUpdateView, OrderListView, \
    DocDeleteView, DocAddView, QuickOrderCreateView, QuickOrderListView

urlpatterns = [
    path('', OrderListView.as_view(), name='orders_list'),
    path('create', OrderCreateView.as_view(), name='order_create'),
    path('<uuid:pk>', OrderDetailView.as_view(), name='order_detail'),
    path('<uuid:pk>/update', OrderUpdateView.as_view(), name='order_update'),
    path('<uuid:pk>/status', OrderStatusView.as_view(), name='order_status'),
    path('<uuid:order_pk>/docs/add', DocAddView.as_view(), name='doc_add'),
    path('<uuid:order_pk>/docs/<uuid:pk>/delete', DocDeleteView.as_view(), name='doc_delete'),
    path('quick', QuickOrderListView.as_view(), name='quick_orders_list'),
    path('quick/create/', QuickOrderCreateView.as_view(), name='quick_order_create'),
]
