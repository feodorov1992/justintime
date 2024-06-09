import datetime
import uuid
from typing import Union, Iterable

from django.db import models
from django.db.models import QuerySet
from django.forms import model_to_dict
from django.template.defaultfilters import floatformat


class RelatedFieldProcessor:
    output_field = None
    fields: Iterable[str] = None
    field_types: Iterable[type] = None

    def __init__(self, obj_list: Iterable[dict]):
        self.obj_list = obj_list or list()

    @classmethod
    def get_class_attr(cls, attr_name: str):
        value = getattr(cls, attr_name)
        if not value:
            raise AttributeError(f'Class attribute "{attr_name}" is required!')
        return value

    @classmethod
    def get_collection(cls, attr_name, attr_type):
        collection = cls.get_class_attr(attr_name)
        cls.check_collection(collection, attr_name, attr_type)
        return collection

    @classmethod
    def check_collection(cls, collection: Iterable, collection_name: str, _type: type):
        if isinstance(collection, str) or not all([isinstance(i, _type) for i in collection]):
            raise AttributeError(f'"{collection_name}" must be collection of "{_type}" instances!')

    def get_fields(self):
        return self.get_collection('fields', str)

    def get_field_types(self):
        return self.get_collection('field_types', type)

    def get_output_field(self):
        return self.__class__.get_class_attr('output_field')

    def check_type(self, value):
        field_types = self.get_field_types()
        if type(value) not in field_types:
            raise AttributeError(f'Type of {value} is not in {field_types}!')
        return value

    def get_fields_values(self, obj: dict):
        return [self.check_type(obj.get(field)) for field in self.get_fields()]

    def process_fields(self, field_values_list: list):
        raise NotImplementedError

    def calc_value(self, obj: dict):
        return self.process_fields(self.get_fields_values(obj))

    def get_values_list(self):
        return [self.calc_value(obj) for obj in self.obj_list]

    def process_result(self, values_list):
        raise NotImplementedError

    def __call__(self):
        return self.get_class_attr('output_field'), self.process_result(self.get_values_list())


class NumberFieldProcessor(RelatedFieldProcessor):
    field_types = int, float
    float_round = None

    @staticmethod
    def multiply(numbers_list):
        result = 1
        for number in numbers_list:
            result *= number
        return result

    def process_fields(self, field_values_list: list):
        return self.multiply(field_values_list)

    def process_result(self, values_list, coefficient: Union[int, float] = None):
        result = sum(values_list)
        if coefficient and type(coefficient) in self.get_field_types():
            result = result * coefficient
        if isinstance(result, float):
            if isinstance(self.float_round, int):
                return round(result, self.float_round)
            elif isinstance(self.float_round, bool) and self.float_round:
                return round(result)
        return result


class StringFieldProcessor(RelatedFieldProcessor):
    field_types = str,
    value_delimiter = ' '
    list_delimiter = ', '

    def process_fields(self, field_values_list: list):
        return self.value_delimiter.join(field_values_list)

    def process_result(self, values_list):
        return self.list_delimiter.join(values_list)


class AbstractModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    last_update = models.DateTimeField(auto_now=True, verbose_name='Время последнего изменения')

    related_fields_mappers: Iterable = None

    def get_related_fields_mappers(self):
        return self.related_fields_mappers or tuple()

    def get_related_objects(self, related_objects: Union[str, QuerySet]):
        if isinstance(related_objects, str):
            if not self.pk:
                return list()
            related_objects = self.__getattribute__(related_objects).all()
        return list(related_objects.values())

    def get_obj_values(self, obj: models.Model = None, related_objects: Union[str, QuerySet, list] = None):
        if obj is None:
            obj = self
        elif not isinstance(obj, AbstractModel):
            raise AttributeError('obj must be instance of AbstractModel class!')

        obj_dict = model_to_dict(obj)

        if related_objects:
            if not isinstance(related_objects, list):
                related_objects = self.get_related_objects(related_objects)

        obj_dict['related_objects'] = related_objects
        return obj_dict

    def map_related(self, obj_dict: dict) -> dict:
        mapper_classes = self.get_related_fields_mappers()
        if mapper_classes and 'related_objects' in obj_dict:
            obj_list = obj_dict.pop('related_objects')
            for mapper_class in mapper_classes:
                mapper = mapper_class(obj_list)
                key, value = mapper()
                obj_dict[key] = value
        return obj_dict

    def get_state(self, obj: models.Model = None, related_objects: Union[str, QuerySet, list] = None):
        obj = self.get_obj_values(obj, related_objects)
        obj = self.map_related(obj)
        return obj

    def get_state_changes(self, old_state: dict = None, new_state: dict = None):
        if old_state is None:
            old_state = self.get_state(self.__class__.objects.get(pk=self.pk))
        if new_state is None:
            new_state = self.get_state()

        result = dict()
        for key in new_state:
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            if old_value != new_value:
                result[key] = {
                    'old': old_value,
                    'new': new_value
                }
        for key in old_state:
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            if key not in result and old_value != new_value:
                result[key] = {
                    'old': old_value,
                    'new': new_value
                }

        return result

    def clean_value(self, key, value):

        field = self._meta.get_field(key)
        if field.is_relation:
            return str(field.related_model.objects.get(pk=value))

        if isinstance(value, float) or isinstance(value, int):
            return floatformat(value, -2)
        elif isinstance(value, datetime.datetime):
            return value.strftime('%d.%m.%Y %H:%M:%S')
        elif isinstance(value, datetime.date):
            return value.strftime('%d.%m.%Y')
        elif not value:
            return '-'
        return str(value)

    def humanize_changes(self, changes_dict, flat=False):
        verbose_names = {field.name: field.verbose_name for field in self._meta.fields}
        result = [
            {
                'verbose': verbose_names.get(key, key),
                'old': self.clean_value(key, value.get('old')),
                'new': self.clean_value(key, value.get('new'))
            } for key, value in changes_dict.items()
        ]
        if flat:
            return [[item.get('verbose'), item.get('old'), item.get('new')] for item in result]
        return result

    def object_created(self, request):
        pass

    def object_updated(self, request, old_state: dict = None, new_state: dict = None):
        pass

    class Meta:
        abstract = True


class AbstractCatalogueModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='Наименование', db_index=True, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
