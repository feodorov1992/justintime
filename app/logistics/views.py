import io
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
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, DeleteView, CreateView
from django_filters import FilterSet
from django_filters.views import FilterView
from django_genericfilters.views import FilteredListView

from cats.models import Currency, CargoParam
from core.pdf_generator import PDFGenerator
from geo.models import Country
from logistics.filtersets import OrderFilterSet, QuickOrderFilterSet
from logistics.forms import OrderForm, CargoFormset, QuickOrderForm, QuickDocFormset
from logistics.models import Order, AttachedDocument, QuickOrder
from orgs.models import Organisation

logger = logging.getLogger(__name__)


class OrderListView(LoginRequiredMixin, FilterView):
    filterset_class = OrderFilterSet
    paginate_by = 5
    login_url = 'login'
    exclude_for_clients = 'client',

    def get_filterset(self, filterset_class):
        filterset = super(OrderListView, self).get_filterset(filterset_class)
        if not self.request.user.is_staff:
            for excluded_filter in self.exclude_for_clients:
                if excluded_filter in filterset.filters:
                    del filterset.filters[excluded_filter]
        return filterset


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
    exclude_from_copy_fields = 'id', 'number', 'date', 'client_number', 'cargo_name', 'cargo_value', \
                               'cargo_value_currency', 'cargo_value_currency_id', 'cargo_origin', 'cargo_origin_id', \
                               'from_date_wanted', 'to_date_wanted', 'comment'

    def copy_obj(self, obj_id):
        copy_obj = self.model.objects.get(pk=obj_id).__dict__

        for field_name in self.exclude_from_copy_fields:
            if field_name in copy_obj:
                copy_obj.pop(field_name)

        for key in list(copy_obj.keys()):
            if key.endswith('_id'):
                new_key = key[:-3]
                copy_obj[new_key] = copy_obj.pop(key)

        return copy_obj

    def get(self, request):
        copy_id = request.GET.get('copy')
        if copy_id is None:
            form = self.form_class(user=request.user)
        else:
            form = self.form_class(initial=self.copy_obj(copy_id), user=request.user)
            # form = self.form_class(instance=self.copy_obj(copy_id), user=request.user)
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


class QuickOrderCreateView(LoginRequiredMixin, View):
    model = QuickOrder
    template_name = 'logistics/quick_order_create.html'
    login_url = 'login'
    form_class = QuickOrderForm
    formset_class = QuickDocFormset

    def check_user(self):
        if self.request.user.is_staff:
            messages.error(self.request, 'Действие запрещено')
            messages.info(self.request, 'Добавить быструю заявку могут только клиенты!')
            return redirect(self.request.META.get('HTTP_REFERER', 'home'))

    def get(self, request):
        check = self.check_user()
        if check:
            return check
        form = self.form_class()
        formset = self.formset_class()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request):
        check = self.check_user()
        if check:
            return check
        form = self.form_class(request.POST)
        formset = self.formset_class(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            obj.created_by = self.request.user
            obj.client = request.user.organization
            obj.save()
            formset.instance = obj
            formset.save()
            messages.success(request, 'Ваша заявка принята')
            messages.info(request, 'Дождитесь ответа нашего менеджера')
            return redirect('orders_list')
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


class QuickOrderListView(OrderListView):
    filterset_class = QuickOrderFilterSet


class ReceiptView(View):

    @staticmethod
    def get_context(obj):
        packages = obj.cargos.select_related('package') \
            .order_by('package__name').values_list('package__name', flat=True).distinct()
        packages = ', '.join(packages).capitalize()
        cargo_params = CargoParam.objects.filter(cargo__in=obj.cargos.all()) \
            .order_by('name').values_list('name', flat=True).distinct()
        cargo_params = ', '.join(cargo_params).capitalize()
        expeditor = Organisation.objects.get(is_expeditor=True)
        return {
            'order': obj,
            'packages': packages,
            'cargo_params': cargo_params,
            'expeditor': expeditor
        }

    def get(self, request, pk, filename):
        order = Order.objects.get(pk=pk)
        generator = PDFGenerator(filename)
        return generator.response('logistics/docs/receipt.html', self.get_context(order))
