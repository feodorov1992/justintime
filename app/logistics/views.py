import logging
from typing import Type

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Model
from django.forms import Form, BaseFormSet, ModelForm, formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, DeleteView, CreateView
from django_filters import FilterSet
from django_filters.views import FilterView
from django_genericfilters.views import FilteredListView

from logistics.filtersets import OrderFilterSet
from logistics.forms import OrderForm, CargoFormset
from logistics.models import Order, AttachedDocument

logger = logging.getLogger(__name__)


class OrderListView(LoginRequiredMixin, FilterView):
    filterset_class = OrderFilterSet
    paginate_by = 5
    login_url = 'login'


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'logistics/order_detail.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['docs'] = self.object.attacheddocument_set.filter(is_public=True)
        return context


class OrderStatusView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'logistics/order_status.html'
    login_url = 'login'


class OrderCreateView(LoginRequiredMixin, View):
    model = Order
    template_name: str = 'logistics/order_create.html'
    form_class: Type[Form] = OrderForm
    formset_class: Type[BaseFormSet] = CargoFormset
    login_url = 'login'

    def get(self, request):
        copy_id = request.GET.get('copy')
        if copy_id is None:
            form = self.form_class(user=request.user)
        else:
            copy_obj = self.model.objects.get(pk=copy_id)
            copy_obj.id = None
            copy_obj.number = None
            copy_obj.client_number = None
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
            obj.object_created(request, obj.get_state(related_objects='cargos'))
            messages.success(request, 'Ваша заявка принята')
            messages.info(request, 'Дождитесь ответа нашего менеджера')
            return redirect('order_detail', pk=obj.pk)
        if form.errors:
            logger.error(form.errors)
        if formset.errors:
            logger.error(formset.errors)
        nfe = formset.non_form_errors()
        if nfe:
            logger.error(nfe)
        messages.error(request, 'Форма заполнена с ошибками')
        messages.info(request, 'Пожалуйста, исправьте')
        return render(request, self.template_name, {'form': form, 'formset': formset})


class OrderUpdateView(LoginRequiredMixin, View):
    model = Order
    template_name: str = 'logistics/order_update.html'
    form_class: Type[Form] = OrderForm
    formset_class: Type[BaseFormSet] = CargoFormset
    login_url = 'login'

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
        self.old_state = order.get_state(related_objects='cargos')
        form = self.form_class(instance=order, data=request.POST, user=request.user)
        formset = self.formset_class(instance=order, data=request.POST)
        if form.is_valid() and formset.is_valid():
            obj = form.save()
            formset.instance = obj
            formset.save()
            obj.object_updated(request, self.old_state, obj.get_state(related_objects='cargos'))
            messages.success(request, f'Заявка № {obj.number} обновлена')
            messages.info(request, 'Дождитесь ответа нашего менеджера')
            return redirect('order_detail', pk=obj.pk)
        if form.errors:
            logger.error(form.errors)
        if formset.errors:
            logger.error(formset.errors)
        nfe = formset.non_form_errors()
        if nfe:
            logger.error(nfe)
        messages.error(request, 'Форма заполнена с ошибками')
        messages.info(request, 'Пожалуйста, исправьте')
        return render(request, self.template_name, {'form': form, 'formset': formset, 'order': order})


class DocDeleteView(LoginRequiredMixin, DeleteView):
    model = AttachedDocument
    template_name = 'logistics/doc_delete.html'
    login_url = 'login'

    def get_success_url(self):
        return reverse('order_detail', kwargs={'pk': self.object.order.pk})

    def form_valid(self, form):
        success_url = self.get_success_url()
        if self.object.allow_delete:
            self.object.delete()
        else:
            self.object.is_public = False
            self.object.save()
        return HttpResponseRedirect(success_url)


class DocAddView(LoginRequiredMixin, CreateView):
    model = AttachedDocument
    template_name = 'logistics/doc_add.html'
    login_url = 'login'
    fields = 'title', 'file'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get_success_url(self):
        return reverse('order_detail', kwargs={'pk': self.kwargs.get('order_pk')})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.order = Order.objects.get(pk=self.kwargs.get('order_pk'))
        self.object.is_public = True
        self.object.allow_delete = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())
