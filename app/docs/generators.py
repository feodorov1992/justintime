import datetime
import uuid

import xlwt
from django.db import models
from django.http import HttpResponse


class XLSGenerator:

    def __init__(self, model, fields: list = None, callable_fields_mapper: dict = None):
        self.model = model
        self.fields = self.__fields_list(fields)
        self.fields_mapper = self.__fields_mapper(callable_fields_mapper)
        self.choices_mapper = self.__choices()
        self.m2m_fields = [i.name for i in self.model._meta.local_many_to_many]

    def __fields_list(self, fields):
        return fields if fields else list(self.model._meta._forward_fields_map.keys())

    def __fields_mapper(self, callable_fields_mapper):
        local_mapper = {key: value.verbose_name for key, value in self.model._meta._forward_fields_map.items()}
        callable_fields_mapper = callable_fields_mapper if callable_fields_mapper else {}
        result = dict()
        for field in self.fields:
            if field in local_mapper:
                result[field] = str(local_mapper[field])
            elif field in callable_fields_mapper:
                result[field] = str(callable_fields_mapper[field])
            else:
                result[field] = str(field)
        return result

    def __choices(self):
        result = dict()
        for field in self.fields:
            details = self.model._meta._forward_fields_map.get(field)
            if details is not None and details.choices is not None:
                result[field] = dict(details.choices)
        return result

    def __get_field(self, obj, field_name):
        if field_name in self.m2m_fields:
            return ', '.join([str(i) for i in obj.__getattribute__(field_name).all()])

        value = obj.__getattribute__(field_name)
        if callable(value):
            value = value()

        if field_name in self.choices_mapper:
            return str(self.choices_mapper[field_name][value])
        else:
            if isinstance(value, datetime.datetime):
                return value.replace(tzinfo=None)
            elif isinstance(value, models.Model):
                return str(value)
            elif isinstance(value, bool):
                if value:
                    return 'Да'
                return 'Нет'
            elif isinstance(value, uuid.UUID):
                return str(value)
            elif value is None:
                return ''
            else:
                return value

    def __get_context(self, queryset):
        result = list()
        for obj in queryset:
            obj_list = list()
            for field in self.fields:
                obj_list.append(self.__get_field(obj, field))
            result.append(obj_list)
        return result

    def __prepare_xls(self, queryset):
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet(self.model._meta.verbose_name_plural.capitalize())

        row_num = 0

        style = xlwt.XFStyle()
        style.font.bold = True

        for col_num, column in enumerate(self.fields):
            ws.write(row_num, col_num, self.fields_mapper[column], style)

        style = xlwt.XFStyle()

        rows = self.__get_context(queryset)
        for row_num, row in enumerate(rows):
            for col_num, column in enumerate(row):
                if isinstance(column, datetime.datetime):
                    style.num_format_str = 'DD/MM/YYYY hh:mm:ss'
                elif isinstance(column, datetime.date):
                    style.num_format_str = 'DD/MM/YYYY'
                elif isinstance(column, float):
                    style.num_format_str = '#,##0.00'
                else:
                    style.num_format_str = 'General'
                ws.write(row_num + 1, col_num, column, style)
        return wb

    def response(self, queryset, filename='report.xls'):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb = self.__prepare_xls(queryset)
        wb.save(response)
        return response
