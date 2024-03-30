from django.db import models

from app.models import AbstractModel, AbstractCatalogueModel


class Currency(AbstractCatalogueModel):
    code = models.CharField(max_length=3, verbose_name='Код валюты', db_index=True, unique=True)
    displayed_name = models.CharField(max_length=10, verbose_name='Отображаемое имя', unique=True)

    @classmethod
    def get_default_pk(cls):
        check_qs = cls.objects.filter(code='RUB')
        if check_qs.exists():
            obj = check_qs.first()
        else:
            obj = cls.objects.create(code='RUB', name='Российский рубль', displayed_name='руб.')
        return obj.pk

    class Meta:
        verbose_name = 'валюта'
        verbose_name_plural = 'валюты'
        ordering = 'name',


class Service(AbstractCatalogueModel):

    class Meta:
        verbose_name = 'услуга'
        verbose_name_plural = 'услуги'
        ordering = 'name',


class Package(AbstractCatalogueModel):

    class Meta:
        verbose_name = 'тип упаковки'
        verbose_name_plural = 'типы упаковки'
        ordering = 'name',


class CargoParam(AbstractCatalogueModel):

    class Meta:
        verbose_name = 'параметр груза'
        verbose_name_plural = 'параметры груза'
        ordering = 'name',
