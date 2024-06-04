from django.urls import path

from orgs.views import OrgAddView

urlpatterns = [
    path('org/add/', OrgAddView.as_view(), name='org_add')
]
