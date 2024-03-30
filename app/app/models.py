import uuid

from django.db import models


class AbstractModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    last_update = models.DateTimeField(auto_now=True, verbose_name='Время последнего изменения')

    class Meta:
        abstract = True


class AbstractCatalogueModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование', db_index=True, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
