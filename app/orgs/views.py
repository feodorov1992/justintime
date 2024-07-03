import json

from django.http import HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.views.generic import CreateView

from orgs.forms import OrgForm
from orgs.models import Organisation


class PopUpMixin:

    def form_valid(self, form):
        to_field = self.request.POST.get('_to_field')
        obj = form.save()
        if to_field:
            attr = str(to_field)
        else:
            attr = obj._meta.pk.attname
        value = obj.serializable_value(attr)
        popup_response_data = json.dumps(
            {
                "value": str(value),
                "obj": str(obj),
            }
        )
        return HttpResponse(popup_response_data)


class OrgAddView(PopUpMixin, CreateView):
    model = Organisation
    form_class = OrgForm
    template_name = 'orgs/org_add.html'
