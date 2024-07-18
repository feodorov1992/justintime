import os
import uuid

import PyPDF2

import pdfkit
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template import Template, Context
from django.template.loader import render_to_string

from django.conf import settings


class PDFGenerator:
    """
    Генератор PDF-файла по шаблону и данным из БД
    """
    OPENED_FILES = list()
    OPENED_FILES_PATHS = list()

    def __init__(self, output_name):
        self.filename = output_name if output_name.endswith('pdf') else f'{output_name}.pdf'
        self.temp_file_path = os.path.join(settings.MEDIA_ROOT, self.filename)
        self.temp_file_path = os.path.normpath(self.temp_file_path)
        self.context = {'filename': self.filename}

    def response(self, template_name, context, media=False):
        """
        Генератор HTTP-ответа, содержащего файл
        :param template_name: наименование шаблона файла
        :param context: набор данных из БД
        :param media: True, если файл нужно брать из БД
        :return: HttpResponse
        """
        self.context.update(context)
        pdf = self.file(self.temp_file_path, template_name, self.context, media)
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        return response

    def file(self, file_path, template_name, context, media):
        """
        Генератор обычного PDF-файла
        :param file_path: путь к файлу на сервере (куда класть, откуда брать)
        :param template_name: наименование шаблона файла
        :param context: набор данных из БД
        :param media: True, если файл нужно брать из БД
        :return: file object
        """
        if media:
            with default_storage.open(template_name, 'r') as file:
                tpl = Template(file.read())
            html = tpl.render(Context(context))
        else:
            html = render_to_string(template_name, context)
        options = {
            "enable-local-file-access": True,
            "margin-top": "11mm",
            "margin-bottom": "11mm",
            "margin-left": "11mm",
            "margin-right": "11mm"
        }
        pdfkit.from_string(html, file_path, options=options)
        file = open(file_path, 'rb')
        self.OPENED_FILES.append(file)
        self.OPENED_FILES_PATHS.append(file_path)
        return file

    def merge_files(self, files, output_path):
        """
        Генератор PDF-файла, слепленного из набора обычных файлов
        :param files: список файлов, из которых нужно слепить результат
        :param output_path: путь к файлу на сервере (куда класть, откуда брать)
        :return: file object
        """
        pdf_writer = PyPDF2.PdfFileWriter()
        for file in files:
            reader = PyPDF2.PdfFileReader(file)
            for page in reader.pages:
                pdf_writer.addPage(page)

        with open(output_path, 'wb') as out_file:
            pdf_writer.write(out_file)

        out_file = open(output_path, 'rb')
        self.OPENED_FILES_PATHS.append(output_path)
        self.OPENED_FILES.append(out_file)
        return out_file

    def merged_response(self, template_name, contexts_list, media=False):
        """
        Генератор HTTP-ответа, содержащего файл, составленный из набора обычных файлов
        :param template_name: наименование шаблона файла
        :param contexts_list: набор данных из БД
        :param media: True, если файл нужно брать из БД
        :return: HttpResponse
        """
        files = list()
        for t, context in enumerate(contexts_list):
            tmp_file_name = f'{uuid.uuid4().hex}.pdf'
            tmp_file_name = os.path.join(settings.MEDIA_ROOT, tmp_file_name)
            self.context.update(context)
            files.append(self.file(tmp_file_name, template_name, context, media))
        pdf = self.merge_files(files, self.temp_file_path)
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        return response

    def __del__(self):
        """
        При удалении объекта генератора из ОЗУ удаляет все созданные файлы с сервера
        """
        for file in self.OPENED_FILES:
            file.close()
        for file_path in self.OPENED_FILES_PATHS:
            if os.path.exists(file_path):
                os.remove(file_path)
