import logging
from typing import Type

from django.contrib import messages
from django.db.models import Model
from django.forms import Form, BaseFormSet, ModelForm, formset_factory
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView
from django_filters import FilterSet
from django_filters.views import FilterView
from django_genericfilters.views import FilteredListView

from logistics.forms import OrderForm, CargoFormset
from logistics.models import Order


logger = logging.getLogger(__name__)


class OrderDetailView(DetailView):
    model = Order
    template_name = 'logistics/order_detail.html'


class OrderStatusView(DetailView):
    model = Order
    template_name = 'logistics/order_status.html'


class OrderCreateView(View):
    model = Order
    template_name: str = 'logistics/order_create.html'
    form_class: Type[Form] = OrderForm
    formset_class: Type[BaseFormSet] = CargoFormset

    def get(self, request):
        copy_id = request.GET.get('copy')
        if copy_id is None:
            form = self.form_class(user=request.user)
        else:
            copy_obj = self.model.objects.get(pk=copy_id)
            copy_obj.id = None
            form = self.form_class(instance=copy_obj, user=request.user)
        formset = self.formset_class()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request):
        form = self.form_class(request.POST, user=request.user)
        formset = self.formset_class(request.POST)
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            if not request.user.is_staff:
                obj.client = request.user.organization
            obj.save()
            formset.instance = obj
            formset.save()
            obj.object_created(request.user, obj.get_state(related_objects='cargos'))
            return redirect('order_detail', pk=obj.pk)
        if form.errors:
            logger.error(form.errors)
        if formset.errors:
            logger.error(formset.errors)
        nfe = formset.non_form_errors()
        if nfe:
            logger.error(nfe)
        return render(request, self.template_name, {'form': form, 'formset': formset})


class OrderUpdateView(View):
    model = Order
    template_name: str = 'logistics/order_update.html'
    form_class: Type[Form] = OrderForm
    formset_class: Type[BaseFormSet] = CargoFormset

    def __init__(self, *args, **kwargs):
        super(OrderUpdateView, self).__init__(*args, **kwargs)
        self.old_state = None

    def get(self, request, pk):
        order = self.model.objects.get(pk=pk)
        form = self.form_class(instance=order, user=request.user)
        formset = self.formset_class(instance=order)
        return render(request, self.template_name, {'form': form, 'formset': formset, 'order': order})

    def post(self, request, pk):
        order = self.model.objects.get(pk=pk)
        form = self.form_class(instance=order, data=request.POST, user=request.user)
        formset = self.formset_class(instance=order, data=request.POST)
        if form.is_valid() and formset.is_valid():
            obj = form.save()
            formset.instance = obj
            formset.save()
            obj.object_updated(request.user, self.old_state, obj.get_state(related_objects='cargos'))
            return redirect('order_detail', pk=obj.pk)
        if form.errors:
            logger.error(form.errors)
        if formset.errors:
            logger.error(formset.errors)
        nfe = formset.non_form_errors()
        if nfe:
            logger.error(nfe)
        return render(request, self.template_name, {'form': form, 'formset': formset, 'order': order})
