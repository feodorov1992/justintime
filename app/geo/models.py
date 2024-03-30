from django.db import models

from app.models import AbstractCatalogueModel


class Country(AbstractCatalogueModel):

    @classmethod
    def get_default_pk(cls):
        check_qs = cls.objects.filter(name='Россия')
        if check_qs.exists():
            obj = check_qs.first()
        else:
            obj = cls.objects.create(name='Россия')
        return obj.pk

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'
        ordering = 'name',


class City(AbstractCatalogueModel):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name='Страна')

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'
        ordering = 'name',
