from django.urls import path
from django_filters.views import FilterView

from logistics.filtersets import OrderFilterSet
from logistics.views import OrderDetailView, OrderStatusView

urlpatterns = [
    path('', FilterView.as_view(filterset_class=OrderFilterSet, paginate_by=5), name='orders_list'),
    path('orders/<uuid:pk>', OrderDetailView.as_view(), name='order_detail'),
    path('orders/<uuid:pk>/status', OrderStatusView.as_view(), name='order_status'),
]
