from typing import Union

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from app.models import AbstractModel
from app_auth.models import User
from cats.models import Currency, Service, Package, CargoParam
from geo.models import Country, City
from orgs.models import Organisation, Contract

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


def default_order_number(number: Union[int, str] = None):
    if number is None:
        obj = Order.objects.last()
        if obj is None:
            number = getattr(settings, 'START_ORDER_NUMBER', 1)
        else:
            number = int(obj.number) + 1
    elif isinstance(number, str):
        number = int(number)
    return '{:0>5}'.format(number)


def int_only_validator(value: str):
    if not value.isnumeric() or not len(value) == 5:
        raise ValidationError('Номер должен быть целым 5-значным числом. Допустимо начинать с 0')


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
    price_currency = models.ForeignKey(Currency, on_delete=models.PROTECT,
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

    status = models.CharField(max_length=25, verbose_name='Статус',
                              choices=ORDER_STATUS_LABELS, default=ORDER_STATUS_LABELS[0][0])
    tracking_url = models.URLField(verbose_name='Ссылка на отслеживание', blank=True, null=True)
    services = models.ManyToManyField(Service, verbose_name='Доп. услуги', blank=True)
    comment = models.TextField(verbose_name='Примечание', blank=True, null=True)
    service_marks = models.TextField(verbose_name='Служебные отметки', blank=True, null=True)
    sum_weight = models.FloatField(verbose_name='Суммарный вес брутто, кг', blank=True, null=True)
    sum_volume = models.FloatField(verbose_name='Суммарный объем груза, м3', blank=True, null=True)
    sum_quantity = models.IntegerField(verbose_name='Суммарное кол-во мест', blank=True, null=True)

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

        self.sum_weight = round(aggregate['sum_weight'], 2)
        self.sum_volume = round(aggregate['sum_volume'] / 1000000, 3)
        self.sum_quantity = aggregate['sum_quantity']
        if commit:
            self.save()

        return aggregate

    def save(
            self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.insurance_needed and not self.insurance_beneficiary:
            self.insurance_beneficiary = self.client
        super(Order, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return f'Заявка №{self.number} от {self.date.strftime("%d.%m.%Y")}'

    class Meta:
        verbose_name = 'заявка на перевозку'
        verbose_name_plural = 'заявки на перевозку'
        ordering = 'number', 'created_at'


class Cargo(AbstractModel):
    mark = models.CharField(max_length=255, blank=True, null=True, verbose_name='Маркировка')
    package = models.ForeignKey(Package, on_delete=models.PROTECT, verbose_name='Тип упаковки')
    length = models.FloatField(verbose_name='Длина, см')
    width = models.FloatField(verbose_name='Ширина, см')
    height = models.FloatField(verbose_name='Высота, см')
    weight = models.FloatField(verbose_name='Вес одного места, кг')
    quantity = models.IntegerField(verbose_name='Количество мест')
    params = models.ManyToManyField(CargoParam, verbose_name='Доп. параметры груза', blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cargos', verbose_name='Заявка')

    class Meta:
        verbose_name = 'груз'
        verbose_name_plural = 'грузы'
        ordering = 'created_at',
