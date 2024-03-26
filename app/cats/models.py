from django.db import models

from app.models import AbstractModel
from cats.validators import NumericStringValidator


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
