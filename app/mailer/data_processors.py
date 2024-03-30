import datetime
import uuid
from typing import Iterable, List

from django.db import models
from django.template.loader import render_to_string


class StyleString:

    def __init__(self, **style_dict):
        self.style_dict = style_dict

    def as_string(self):
        return str(self)

    def __str__(self):
        return '; '.join([f'{key.lower()}: {value.lower()}' for key, value in self.style_dict.items()])


class TableCell:
    html_template = 'mailer/base/cell.html'

    def __init__(self, value, tag, style):
        self.value = self.clean(value)
        self.tag = tag
        self.style = style

    @staticmethod
    def clean(value):
        if value is None:
            return '-'
        if isinstance(value, uuid.UUID) or isinstance(value, models.Model):
            return str(value)
        if isinstance(value, datetime.datetime):
            return value.strftime('%d.%m.%Y %H:%M:%S')
        if isinstance(value, datetime.date):
            return value.strftime('%d.%m.%Y')
        return value

    def __str__(self):
        return render_to_string(self.html_template, {'value': self.value, 'tag': self.tag, 'style': self.style})

    def __repr__(self):
        _class = f'{self.__class__.__module__}.{self.__class__.__qualname__}'
        return f'<{_class} value={repr(self.value)} tag={repr(self.tag)} style={repr(self.style)}>'


class TableRow:
    html_template = 'mailer/base/tr.html'
    cell_class = TableCell

    def __init__(self, label: str, dataset: Iterable,
                 tr_style: dict = None, td_style: dict = None,
                 label_tag: str = 'th', values_tag: str = 'td'):
        self.__label = label
        self.__dataset = dataset
        self.__row_style = StyleString(**tr_style) if isinstance(tr_style, dict) else None
        self.__label_style = StyleString(**td_style) if isinstance(td_style, dict) else None
        self.__values_style = StyleString(**td_style) if isinstance(td_style, dict) else None
        self.__label_tag = label_tag if label_tag else 'th'
        self.__values_tag = values_tag if values_tag else 'td'
        self.__style_override = dict()

    def prepare_dataset(self):
        result = [self.cell_class(self.__label, self.__label_tag, self.__label_style)]

        for idx, value in enumerate(self.__dataset):
            style = self.__style_override.get(idx, self.__values_style)
            result.append(
                self.cell_class(value, self.__values_tag, style)
            )

        return result

    def values_style_override(self, col_number: int, style: dict):
        self.__style_override[col_number] = StyleString(**style)

    def as_tr(self):
        context = {'items': self.prepare_dataset(), 'tr_style': self.__row_style}
        return render_to_string(self.html_template, context=context)

    def __str__(self):
        return self.as_tr()

    def __repr__(self):
        return self.__str__()


class DataProcessor:
    html_template: str = None

    def __init__(self, data):
        self._data = data

    @staticmethod
    def style_string(style: dict):
        if not isinstance(style, dict):
            style = {}
        style = StyleString(**style)
        return style.as_string()

    def html_data(self):
        raise NotImplementedError

    def txt_data(self):
        raise NotImplementedError

    def get_context(self):
        data = self.html_data()
        return {'data': data}

    def html(self):
        return render_to_string(self.html_template, self.get_context())

    def txt(self):
        return '\n'.join(self.txt_data())


class TextProcessor(DataProcessor):

    def __init__(self, data: str):
        super(TextProcessor, self).__init__(data)

    def html_data(self):
        pass

    def html(self):
        return self._data

    def txt_data(self):
        return [self._data]


class ListProcessor(DataProcessor):
    html_template = 'mailer/base/list.html'
    list_style = {'display': 'inline-block', 'padding-inline-start': '0'}

    def __init__(self, data: List[list], list_tag: str = 'ul'):
        super(ListProcessor, self).__init__(data)
        self.list_tag = list_tag

    def get_context(self):
        context = super(ListProcessor, self).get_context()
        context['tag'] = self.list_tag
        context['style'] = self.style_string(self.list_style)
        return context

    def html_data(self):
        result = list()
        for item in self._data:
            if len(item) > 1:
                result.append(f'<b>{item[0]}:</b> {"; ".join(item[1:])}')
            elif item:
                result.append(item[0])
            else:
                continue
        return result

    def txt_data(self):
        result = list()
        for item in self._data:
            if len(item) > 1:
                result.append(f'{item[0]}: {"; ".join(item[1:])}')
            elif item:
                result.append(item[0])
            else:
                continue
        return result


class URLProcessor(DataProcessor):
    html_template = 'mailer/base/link.html'
    url_style = None

    def __init__(self, url: str, url_label: str = None, url_text: str = None):
        super(URLProcessor, self).__init__(url)
        self.url_label = url_label if url_label else url
        self.url_text = url_text

    def get_context(self):
        context = super(URLProcessor, self).get_context()
        context['url_text'] = self.url_text
        context['url_label'] = self.url_label
        context['style'] = self.style_string(self.url_style)
        return context

    def html_data(self):
        return self._data

    def txt_data(self):
        result = list()
        if self.url_text:
            result.append(self.url_text)
        if self.url_label:
            result.append(f'{self.url_label}: {self._data}')
        else:
            result.append(self._data)
        return result


class TableProcessor(DataProcessor):
    html_template = 'mailer/base/table.html'
    cell_class = TableCell
    row_class = TableRow
    table_style: dict = None
    header_row_style: dict = None
    header_cell_style: dict = None
    header_label_tag: str = 'th'
    header_values_tag: str = 'th'
    data_row_style: dict = None
    data_cell_style: dict = None
    data_label_tag: str = 'th'
    data_values_tag: str = 'td'
    row_class.cell_class = cell_class

    def __init__(self, data: Iterable[list], header: list = None):
        super(TableProcessor, self).__init__(data)
        self.__header = header
        self.check_data()

    def header(self):
        return self.row_class(
            self.__header[0], self.__header[1:], self.header_row_style, self.header_cell_style,
            self.header_label_tag, self.header_values_tag
        )

    def body(self):
        return [
            self.row_class(
                data[0], data[1:], self.data_row_style, self.data_cell_style,
                self.data_label_tag, self.data_values_tag
            ) for data in self._data
        ]

    def check_data(self):
        control_length = len(self.__header)
        for item in self._data:
            if len(item) != control_length:
                raise AttributeError('All items in data dict must have equal length to header!')

    def merge_header(self, data_item: list):
        result = [str(data_item[0])]
        for idx, value in enumerate(data_item[1:], start=1):
            result.append(f'{self.__header[idx]}: {self.cell_class.clean(value)}')
        return '. '.join(result)

    def txt_data(self):
        if self.__header:
            return [self.merge_header(data_item) for data_item in self._data]
        return self._data

    def get_context(self):
        context = super(TableProcessor, self).get_context()
        context['table_style'] = self.style_string(self.table_style)
        return context

    def html_data(self):
        if self.__header:
            return [self.header(), *self.body()]
        return self.body()


class EmailBodyGenerator:
    global_table_template: str = 'mailer/base/global/table.html'
    global_row_template: str = 'mailer/base/global/tr.html'
    global_table_style: dict = None
    main_table_style: dict = None
    main_row_style: dict = None
    main_content_style: dict = None
    header_row_style: dict = None
    header_cell_style: dict = None
    table_processor_class = TableProcessor
    text_processor_class = TextProcessor
    list_processor_class = ListProcessor
    url_processor_class = URLProcessor

    def __init__(self, header: str):
        self.header = header
        self.__data = list()
        self.__add_header()

    def __add_data(self, processor_class, content, *params, row_style: dict = None, content_style: dict = None):
        if row_style is None:
            row_style = self.main_row_style
        if content_style is None:
            content_style = self.main_content_style
        self.__data.append([
            processor_class(content, *params),
            DataProcessor.style_string(row_style),
            DataProcessor.style_string(content_style),
        ])

    def __add_header(self):
        self.__add_data(self.text_processor_class, self.header,
                        row_style=None if self.header_row_style is None else self.header_row_style,
                        content_style=None if self.header_cell_style is None else self.header_cell_style)

    def add_text(self, text):
        self.__add_data(self.text_processor_class, text)

    def add_list(self, data: List[list], list_type='ul'):
        self.__add_data(self.list_processor_class, data, list_type)

    def add_url(self, url, url_label: str = None, url_text: str = None):
        self.__add_data(self.url_processor_class, url, url_label, url_text)

    def add_table(self, data: List[list], header: list):
        self.__add_data(self.table_processor_class, data, header)

    def html_data(self):
        result = list()
        for content, row_style, content_style in self.__data:
            context = {
                'content': content,
                'row_style': row_style,
                'content_style': content_style
            }
            html = render_to_string(self.global_row_template, context)
            result.append(html)
        return result

    def get_context(self):
        return {
            'global_table_style': DataProcessor.style_string(self.global_table_style),
            'main_table_style': DataProcessor.style_string(self.main_table_style),
            'data': self.html_data()
        }

    def html(self):
        return render_to_string(self.global_table_template, self.get_context())

    def txt_data(self):
        return [content.txt() for content, _, _ in self.__data]

    def txt(self):
        return '\n\n'.join(self.txt_data())
