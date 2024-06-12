import os
from typing import Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import floatformat
from django.utils import timezone

from app.models import AbstractModel, NumberFieldProcessor
from app_auth.models import User
from cats.models import Currency, Service, Package, CargoParam
from geo.models import Country, City
from orgs.models import Organisation, Contract
from logistics.notifications import order_update_client_notification, order_update_manager_notification, \
    order_create_client_notification, order_create_manager_notification, quick_order_create_manager_notification

INS_RATES = (
    (1, '100%'),
    (1.1, '110%')
)

ORDER_STATUS_LABELS = (
    ('new', 'Новая'),
    ('prepare', 'Подготовка к перевозке'),
    ('in_progress', 'В пути'),
    ('delivered', 'Доставлено'),
    ('docs_received', 'Документы получены'),
    ('complete', 'Завершено'),
)


def default_number(model, number: Union[int, str] = None):
    if number is None:
        obj = model.objects.first()
        if obj is None:
            number = getattr(settings, 'START_ORDER_NUMBER', 1)
        else:
            number = int(obj.number) + 1
    elif isinstance(number, str):
        number = int(number)
    return '{:0>5}'.format(number)


def default_order_number(number: Union[int, str] = None):
    return default_number(Order, number)


def default_quick_order_number(number: Union[int, str] = None):
    return default_number(QuickOrder, number)


def int_only_validator(value: str):
    if not value.isnumeric() or not len(value) == 5:
        raise ValidationError('Номер должен быть целым 5-значным числом. Допустимо начинать с 0')


class WeightProcessor(NumberFieldProcessor):
    output_field = 'sum_weight'
    fields = 'weight', 'quantity'
    float_round = 3


class VolumeProcessor(NumberFieldProcessor):
    output_field = 'sum_volume'
    fields = 'length', 'width', 'height', 'quantity'
    float_round = 3

    def process_result(self, values_list, coefficient=None):
        return super().process_result(values_list, 1 / 1000000)


class QuantityProcessor(NumberFieldProcessor):
    output_field = 'sum_quantity'
    fields = 'quantity',


class QuickOrder(AbstractModel):
    number = models.CharField(max_length=5, db_index=True, unique=True, verbose_name='Номер заявки',
                              default=default_quick_order_number, validators=[int_only_validator])
    client_number = models.CharField(max_length=255, db_index=True, blank=True, verbose_name='Клиентский номер')
    client = models.ForeignKey(Organisation, on_delete=models.CASCADE, editable=False,
                               verbose_name='Заказчик', related_name='quick_orders')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Создатель заявки',
                                   editable=False, related_name='quick_orders')

    def __str__(self):
        return f'Быстрая заявка №{self.number}'

    class Meta:
        verbose_name = 'быстрая заявка'
        verbose_name_plural = 'быстрые заявки'
        ordering = '-number', '-created_at'


@receiver(post_save, sender=QuickOrder)
def save_order(sender, instance: User, created, **kwargs):
    if created:
        quick_order_create_manager_notification.delay(instance.pk)


class Order(AbstractModel):
    number = models.CharField(max_length=5, db_index=True, unique=True, verbose_name='Номер заявки',
                              default=default_order_number, validators=[int_only_validator])
    client_number = models.CharField(max_length=255, db_index=True, blank=True, verbose_name='Клиентский номер')
    date = models.DateField(default=timezone.now, verbose_name='Дата заявки')
    gov_contract_number = models.CharField(max_length=255, blank=True, verbose_name='№ ИГК')
    client = models.ForeignKey(Organisation, on_delete=models.CASCADE,
                               verbose_name='Заказчик', related_name='client_in_orders')
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT,
                                 verbose_name='Договор', related_name='contract_in_orders')
    client_employee = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL,
                                        verbose_name='Сотрудник заказчика', related_name='client_employee_in_orders')
    manager = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL,
                                verbose_name='Менеджер', related_name='manager_in_orders')
    cargo_name = models.CharField(max_length=255, verbose_name='Наименование груза')
    cargo_origin = models.ForeignKey(Country, on_delete=models.PROTECT,
                                     verbose_name='Страна происхождения груза', related_name='cargo_origin_in_orders')
    cargo_value = models.FloatField(verbose_name='Заявленная стоимость груза')
    cargo_value_currency = models.ForeignKey(Currency, on_delete=models.PROTECT,
                                             default=Currency.get_default_pk,
                                             verbose_name='Валюта стоимости груза',
                                             related_name='cargo_value_currency_in_orders')
    insurance_needed = models.BooleanField(default=False, verbose_name='Страхование требуется')
    insurance_premium = models.FloatField(blank=True, default=0, verbose_name='Страховая премия')
    insurance_sum_rate = models.FloatField(choices=INS_RATES, default=INS_RATES[0][0],
                                           verbose_name='Коэффициент страховой суммы')
    insurance_beneficiary = models.ForeignKey(Organisation, on_delete=models.PROTECT, blank=True, null=True,
                                              verbose_name='Выгодоприобретатель',
                                              related_name='beneficiary_in_orders')
    price = models.FloatField(blank=True, null=True, verbose_name='Ставка')
    price_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=Currency.get_default_pk,
                                       verbose_name='Валюта ставки', related_name='price_currency_in_orders')

    from_org = models.ForeignKey(Organisation, on_delete=models.PROTECT,
                                 verbose_name='Грузоотправитель', related_name='from_org_in_orders')
    from_contacts = models.TextField(verbose_name='Контакты грузоотправителя')
    from_index = models.IntegerField(verbose_name='Индекс пункта отправки')
    from_country = models.ForeignKey(Country, on_delete=models.PROTECT,
                                     verbose_name='Страна отправки', related_name='from_country_in_orders')
    from_city = models.ForeignKey(City, on_delete=models.PROTECT,
                                  verbose_name='Город отправки', related_name='from_city_in_orders')
    from_address = models.CharField(max_length=255, verbose_name='Адрес отправки')
    from_label = models.CharField(max_length=50, verbose_name='Название пункта отправки', blank=True, null=True)
    from_date_wanted = models.DateField(blank=True, null=True, verbose_name='Дата готовности груза')
    from_date_plan = models.DateField(blank=True, null=True, verbose_name='Дата отправки (план)')
    from_date_fact = models.DateField(blank=True, null=True, verbose_name='Дата отправки (факт)')

    to_org = models.ForeignKey(Organisation, on_delete=models.PROTECT,
                               verbose_name='Грузополучатель', related_name='to_org_in_orders')
    to_contacts = models.TextField(verbose_name='Контакты грузополучателя')
    to_index = models.IntegerField(verbose_name='Индекс пункта доставки')
    to_country = models.ForeignKey(Country, on_delete=models.PROTECT,
                                   verbose_name='Страна доставки', related_name='to_country_in_orders')
    to_city = models.ForeignKey(City, on_delete=models.PROTECT,
                                verbose_name='Город доставки', related_name='to_city_in_orders')
    to_address = models.CharField(max_length=255, verbose_name='Адрес доставки')
    to_label = models.CharField(max_length=50, verbose_name='Название пункта доставки', blank=True, null=True)
    to_date_wanted = models.DateField(blank=True, null=True, verbose_name='Желаемая дата доставки')
    to_date_plan = models.DateField(blank=True, null=True, verbose_name='Дата доставки (план)')
    to_date_fact = models.DateField(blank=True, null=True, verbose_name='Дата доставки (факт)')

    status = models.CharField(max_length=20, choices=ORDER_STATUS_LABELS, default=ORDER_STATUS_LABELS[0][0],
                              verbose_name='Статус')
    status_updated = models.DateTimeField(editable=False, verbose_name='Время изменения статуса',
                                          null=True, blank=True)

    tracking_url = models.URLField(verbose_name='Ссылка на отслеживание', blank=True, null=True)
    services = models.ManyToManyField(Service, verbose_name='Доп. услуги', blank=True)
    comment = models.TextField(verbose_name='Примечание', blank=True, null=True)
    service_marks = models.TextField(verbose_name='Служебные отметки', blank=True, null=True)
    sum_weight = models.FloatField(verbose_name='Вес брутто груза, кг', blank=True, null=True)
    sum_volume = models.FloatField(verbose_name='Объем груза, м3', blank=True, null=True)
    sum_quantity = models.IntegerField(verbose_name='Кол-во мест', blank=True, null=True)
    quick_order = models.ForeignKey(QuickOrder, blank=True, null=True, on_delete=models.SET_NULL,
                                    verbose_name='Быстрая заявка')

    related_fields_mappers = WeightProcessor, QuantityProcessor, VolumeProcessor

    def sum_cargo_params(self, queryset: QuerySet = None, commit: bool = False):
        if queryset is None:
            queryset = self.cargos.all()

        aggregate = queryset.annotate(
            full_weight=models.F('weight') * models.F('quantity'),
            full_volume=models.F('length') * models.F('width') * models.F('height') * models.F('quantity')
        ).aggregate(
            sum_weight=models.Sum('full_weight'),
            sum_volume=models.Sum('full_volume'),
            sum_quantity=models.Sum('quantity')
        )

        self.sum_weight = round(aggregate['sum_weight'] or 0, 2)
        self.sum_volume = round((aggregate['sum_volume'] or 0) / 1000000, 3)
        self.sum_quantity = aggregate['sum_quantity'] or 0
        if commit:
            self.save()

        return aggregate

    def check_related_fields(self, child_name, child_parent_name, self_parent_name, error_dict, error_msg):
        if hasattr(self, child_name):
            child = getattr(self, child_name)
            child_parent = getattr(child, child_parent_name, None)
            self_parent = getattr(self, self_parent_name, None)
            if child_parent and self_parent and child_parent != self_parent:
                error_dict[child_name] = error_msg

    def clean(self):
        errors = dict()
        super(Order, self).clean()

        self.check_related_fields('contract', 'organization_id', 'client_id', errors,
                                  'При изменении заказчика необходимо изменить договор!')
        self.check_related_fields('client_employee', 'organization_id', 'client_id', errors,
                                  'При изменении заказчика необходимо изменить сотрудника!')
        self.check_related_fields('from_city', 'country_id', 'from_country_id', errors,
                                  'При изменении страны необходимо изменить город!')
        self.check_related_fields('to_city', 'country_id', 'to_country_id', errors,
                                  'При изменении страны необходимо изменить город!')

        if errors:
            raise ValidationError(errors)

    def get_field_choices(self, field_name):
        fields = {field.name: field for field in self._meta.fields}
        field = fields.get(field_name)
        if field:
            return field.choices

    def _get_field(self, field_name: str, field_prefix: str = None):
        is_callable = False
        value = None
        if field_prefix is None:
            field_prefix = ''
        full_name = field_prefix + field_name
        if hasattr(self, full_name):
            if self.get_field_choices(full_name):
                full_name = f'get_{full_name}_display'
                is_callable = True
            value = getattr(self, full_name)
            if value and is_callable:
                value = value()
        if value is None:
            return ''
        return str(value)

    def _short_address(self, field_prefix: str = None):
        addr_label = self._get_field('label', field_prefix)
        if addr_label:
            return addr_label
        result = list()
        country = self._get_field('country', field_prefix)
        if country:
            result.append(country)
        city = self._get_field('city', field_prefix)
        if city:
            result.append(city)
        return ', '.join(result)

    def _full_address(self, field_prefix: str = None):
        result = list()
        index = self._get_field('index', field_prefix)
        country = self._get_field('country', field_prefix)
        city = self._get_field('city', field_prefix)
        address = self._get_field('address', field_prefix)
        address = ' '.join([i.lower() for i in address.split()])
        if index and index.lower() not in address:
            result.append(index)
        if country and country.lower() not in address:
            result.append(country)
        if city and city.lower() not in address:
            result.append(city)
        address = [i for i in address.split(', ')]
        reworked_address = list()
        for item in address:
            reworked_item = ' '.join([i.capitalize() for i in item.split()])
            reworked_address.append(reworked_item)
        return ', '.join(result + reworked_address)

    def from_address_short(self):
        return self._short_address('from_')

    from_address_short.short_description = 'Пункт отправки'

    def to_address_short(self):
        return self._short_address('to_')

    to_address_short.short_description = 'Пункт доставки'

    def from_address_full(self):
        return self._full_address('from_')

    from_address_full.short_description = 'Адрес отправки'

    def to_address_full(self):
        return self._full_address('to_')

    to_address_full.short_description = 'Адрес доставки'

    def full_price(self):
        if self.price is not None:
            return f'{floatformat(self.price, -2)} {self.price_currency.displayed_name}'

    full_price.short_description = 'Ставка'

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super(Order, self).save(force_insert, force_update, using, update_fields)

    def object_created(self, request, new_state: dict = None):
        changes = self.get_state_changes(old_state=dict(), new_state=new_state)
        for key, value in changes.items():
            if key.startswith('sum'):
                self.__setattr__(key, value.get('new'))
        if self.insurance_needed and not self.insurance_beneficiary:
            self.insurance_beneficiary = self.client
        self.status_updated = self.created_at
        self.save()
        if request.user.is_staff:
            order_create_client_notification.delay(self.pk, request.user.pk)
        else:
            order_create_manager_notification.delay(self.pk, request.user.pk)

    def object_updated(self, request, old_state: dict = None, new_state: dict = None):
        changes = self.get_state_changes(old_state=old_state, new_state=new_state)
        updated = False
        if 'status' in changes:
            OrderStatus.objects.create(
                name=changes.get('status').get('old'), change_time=self.status_updated, order=self
            )
            self.status_updated = timezone.now()
            updated = True
        for key, value in changes.items():
            current_value = self.__getattribute__(key)
            new_value = value.get('new')
            if current_value != new_value:
                m2m = {field.name: field for field in self._meta.many_to_many}
                if key not in m2m:
                    field = self._meta.get_field(key)
                    if not key.endswith('_id') and field.is_relation:
                        key = f'{key}_id'
                    self.__setattr__(key, new_value)
                else:
                    self.__getattribute__(key).set(new_value)
                updated = True
        if self.insurance_needed and not self.insurance_beneficiary:
            self.insurance_beneficiary = self.client
            updated = True
        if updated:
            self.save()
        if request.user.is_staff:
            order_update_client_notification.delay(self.pk, request.user.pk, changes)
        else:
            order_update_manager_notification.delay(self.pk, request.user.pk, changes)

    def __str__(self):
        return f'Заявка №{self.number} от {self.date.strftime("%d.%m.%Y")}'

    class Meta:
        verbose_name = 'заявка на перевозку'
        verbose_name_plural = 'заявки на перевозку'
        ordering = '-number', '-created_at'


class Cargo(AbstractModel):
    mark = models.CharField(max_length=255, blank=True, null=True, verbose_name='Маркировка')
    package = models.ForeignKey(Package, on_delete=models.PROTECT, verbose_name='Тип упаковки')
    length = models.FloatField(verbose_name='Длина, см', validators=[MinValueValidator(0)])
    width = models.FloatField(verbose_name='Ширина, см', validators=[MinValueValidator(0)])
    height = models.FloatField(verbose_name='Высота, см', validators=[MinValueValidator(0)])
    weight = models.FloatField(verbose_name='Вес, кг', validators=[MinValueValidator(0)])
    quantity = models.IntegerField(verbose_name='Кол-во мест', validators=[MinValueValidator(0)])
    params = models.ManyToManyField(CargoParam, verbose_name='Доп. параметры груза', blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cargos', verbose_name='Заявка')

    def __str__(self):
        return f'{self.package} {self.length}х{self.width}х{self.height} см, {self.weight} кг ({self.quantity} шт)'

    class Meta:
        verbose_name = 'груз'
        verbose_name_plural = 'грузы'
        ordering = 'created_at',


class OrderStatus(AbstractModel):
    name = models.CharField(max_length=25, verbose_name='Статус',
                            choices=ORDER_STATUS_LABELS, default=ORDER_STATUS_LABELS[0][0])
    change_time = models.DateTimeField(default=timezone.now, verbose_name='Время изменения статуса', db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заявка')

    def __str__(self):
        return f'{self.change_time.strftime("%d.%m.%Y %H:%M:%S")}: {self.get_name_display()}'

    class Meta:
        verbose_name = 'статус заявки'
        verbose_name_plural = 'статусы заявки'
        ordering = 'order', '-change_time',


def path_by_order(instance, filename, month=None, year=None):
    if not month:
        month = instance.order.date.month
    if not year:
        year = instance.order.date.year
    return os.path.join(
        'files',
        'orders',
        str(year),
        '{:0>2}'.format(month),
        instance.order.id.hex,
        filename
    )


def path_by_quick_order(instance, filename, month=None, year=None):
    return os.path.join(
        'files',
        'quick_orders',
        instance.quick_order.id.hex,
        filename
    )


class AttachedDocument(AbstractModel):
    title = models.CharField(max_length=255, verbose_name='Наименование документа')
    file = models.FileField(verbose_name='Файл', upload_to=path_by_order)
    is_public = models.BooleanField(default=False, db_index=True, verbose_name='Показать клиенту')
    allow_delete = models.BooleanField(default=False, verbose_name='Клиент может удалить')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заявка')

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Приложенный файл'
        verbose_name_plural = 'Приложенные файлы'
        ordering = '-created_at',


class QuickAttachedDocument(AbstractModel):
    title = models.CharField(max_length=255, verbose_name='Наименование документа')
    file = models.FileField(verbose_name='Файл', upload_to=path_by_quick_order)
    quick_order = models.ForeignKey(QuickOrder, on_delete=models.CASCADE, verbose_name='Заявка')

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Приложенный файл'
        verbose_name_plural = 'Приложенные файлы'
        ordering = '-created_at',
