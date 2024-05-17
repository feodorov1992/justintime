from django.urls import path
from django_filters.views import FilterView

from logistics.filtersets import OrderFilterSet

urlpatterns = [
    path('', FilterView.as_view(filterset_class=OrderFilterSet, paginate_by=5), name='orders_list'),
]
