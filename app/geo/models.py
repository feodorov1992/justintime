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
    name = models.CharField(max_length=100, verbose_name='Наименование', db_index=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, verbose_name='Страна')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'
        ordering = 'country', 'name'
        unique_together = 'country', 'name'
