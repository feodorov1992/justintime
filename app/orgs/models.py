from django.db import models
from django.utils import timezone

from app.models import AbstractModel
from cats.models import Currency
from orgs.validators import NumericStringValidator


inn_validator = NumericStringValidator('ИНН', [10, 12])
kpp_validator = NumericStringValidator('КПП', [9])
ogrn_validator = NumericStringValidator('ОГРН', [13, 15])


class Organisation(AbstractModel):
    inn = models.CharField(db_index=True, verbose_name='ИНН', validators=[inn_validator],
                           blank=True, null=True, max_length=12)
    kpp = models.CharField(db_index=True, verbose_name='КПП', validators=[kpp_validator],
                           blank=True, null=True, max_length=9)
    ogrn = models.CharField(db_index=True, verbose_name='ОГРН', validators=[ogrn_validator],
                            blank=True, null=True, max_length=15)
    name = models.CharField(db_index=True, verbose_name='Отображаемое имя', max_length=255)
    legal_name = models.CharField(db_index=True, verbose_name='Юр. наименование', max_length=255)
    legal_address = models.CharField(verbose_name='Юр. адрес', max_length=255)
    fact_address = models.CharField(verbose_name='Факт. адрес', max_length=255)
    is_client = models.BooleanField(verbose_name='Является заказчиком', default=False)
    is_expeditor = models.BooleanField(verbose_name='Является экспедитором', default=False, editable=False)
    email = models.EmailField(verbose_name='Email', blank=True, null=True)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.is_expeditor:
            if self.__class__.objects.filter(is_expeditor=True).exclude(pk=self.pk).exists():
                self.is_expeditor = False
        super(Organisation, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'организация'
        verbose_name_plural = 'организации'
        ordering = 'name',


class Contract(AbstractModel):
    number = models.CharField(max_length=50, verbose_name='Номер договора', db_index=True)
    date = models.DateField(verbose_name='Дата договора')
    expiry_date = models.DateField(verbose_name='Дата окончания действия', blank=True, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name='Валюта',
                                 default=Currency.get_default_pk)
    organization = models.ForeignKey(Organisation, on_delete=models.CASCADE, verbose_name='Контрагент')

    def is_active(self):
        today = timezone.now().date()
        if self.expiry_date:
            return self.date <= today <= self.expiry_date
        return self.date <= today

    is_active.short_description = 'Действующий'
    is_active.boolean = True

    def __str__(self):
        return f'Договор № {self.number} от {self.date.strftime("%d.%m.%Y")}'

    class Meta:
        verbose_name = 'договор'
        verbose_name_plural = 'договоры'
        ordering = 'date', 'number'
        unique_together = 'organization', 'number'
