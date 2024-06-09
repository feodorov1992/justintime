import logging
from typing import List
from urllib import parse

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect

from mailer.data_processors import EmailBodyGenerator, TableProcessor as BaseTableProcessor,\
    ListProcessor as BaseListProcessor, URLProcessor as BaseURLProcessor


logger = logging.getLogger(__name__)


class TableProcessor(BaseTableProcessor):
    table_style: dict = {'font-family': '"Open Sans", sans-serif', 'border-collapse': 'collapse'}
    header_row_style: dict = {'border': '1px solid #012F55'}
    header_cell_style: dict = {'background': '#012F55', 'color': 'white', 'font-weight': '700', 'padding': '5px',
                               'line-height': '24px', 'font-size': '14px', 'vertical-align': 'center',
                               'text-align': 'start'}
    data_cell_style: dict = {'border': '1px solid #012F55', 'padding': '5px', 'color': '#102E52',
                             'line-height': '24px', 'font-size': '12px', 'vertical-align': 'center',
                             'text-align': 'start'}


class ListProcessor(BaseListProcessor):
    list_style = {'display': 'inline-block', 'padding-inline-start': '15px'}
    marker_style = {'font-weight': '700'}
    item_style = {'font-weight': '400'}
    title_style = {'font-weight': '700', 'font-size': '18px'}


class URLProcessor(BaseURLProcessor):
    url_outer_style = {'font-size': '16px', 'padding': '10px', 'background': '#012F55', 'border-radius': '8px',
                       'min-width': '200px', 'text-align': 'center', 'border': '1px solid #012F55',
                       'display': 'inline-block'}
    url_inner_style = {'color': 'white', 'text-decoration': 'none'}


class NotificationGenerator(EmailBodyGenerator):
    global_table_template = 'core/mail/base/table.html'
    global_row_template: str = 'mailer/base/global/tr.html'
    global_table_style: dict = {'margin': '0 auto', 'text-align': 'center', 'min-width': '600px', 'width': '100%',
                                'padding': '0'}
    main_table_style = {'margin': '0 auto', 'width': '600px'}
    main_row_style: dict = None
    main_content_style: dict = {'font-family': '"Open Sans", sans-serif', 'font-size': '14px', 'color': '#102E52',
                                'text-align': 'start', 'padding': '15px 30px'}
    header_row_style: dict = None
    header_cell_style: dict = {'font-family': '"Open Sans", sans-serif', 'font-size': '20px', 'line-height': '24px',
                               'color': '#102E52', 'font-weight': '700', 'text-align': 'start', 'padding': '15px 30px'}
    table_processor_class = TableProcessor
    list_processor_class = ListProcessor
    url_processor_class = URLProcessor

    def __init__(self, *args, **kwargs):
        super(NotificationGenerator, self).__init__(*args, **kwargs)
        self.images = [
            self.add_img('img/email_header.png', 'header_img'),
            self.add_img('img/email_footer.png', 'footer_img')
        ]


class MailNotification:
    generator_class: EmailBodyGenerator = NotificationGenerator

    def __init__(self, subject, title):
        self.subject = subject
        self.title = title
        self.generator = self.generator_class(self.title)
        self.recipients = list()

    def add_recipients(self, *recipients):
        self.recipients += recipients

    def add_outer_link(self, url, label, text, title: str = None):
        self.generator.add_url(url, label, text, title)

    def add_inner_link(self, path, label, text, title: str = None):
        url = parse.urljoin(f'http://{settings.DOMAIN}', path)
        self.generator.add_url(url, label, text, title)

    def add_table(self, data: List[list], header: list, title=None):
        self.generator.add_table(data, header, title)

    def add_list(self, data: List[list], list_type='ul', title=None):
        self.generator.add_list(data, list_type, title)

    def add_text(self, text, title=None):
        self.generator.add_text(text, title)

    def send(self):
        if not self.recipients:
            return
        msg = EmailMultiAlternatives(
            subject=self.subject,
            body=self.generator.txt(),
            from_email=settings.EMAIL_HOST_USER,
            to=self.recipients
        )
        msg.mixed_subtype = 'related'
        msg.attach_alternative(self.generator.html(), "text/html")
        for img in self.generator.images:
            msg.attach(img)

        return self.sending_attempt(msg, settings.EMAIL_HOST_USER, self.recipients)

    @staticmethod
    def sending_attempt(msg, from_email, recipients):
        result = 'SUCCESS'
        log_msg = [
            f'from_email: {from_email}',
            f'recipients: {", ".join([i for i in recipients if i is not None])}'
        ]
        log = logging.info
        if settings.ALLOW_TO_SEND_MAIL:
            try:
                if not msg.send(fail_silently=False):
                    result = 'UNKNOWN_ERROR'
                log_msg.append(f'status: {result}')
            except Exception as e:
                result = 'ERROR'
                log_msg.append(f'error: {e}')
                log = logging.error
        else:
            log_msg.append('ALLOW_TO_SEND_MAIL set to False. Email not sent')
        log('; '.join(log_msg))
        return result

# def test_mail(request):
#     email = NotificationGenerator('Определена плановая дата доставки груза<br><u>8593 P-C/2024/РТЛ (60515)</u>')
#     email.add_table([
#         ['Номер-хуемер', 'Что-то очень полезное', 'Циферки'],
#         ['Важный перец', 'Что-то очень полезное', 'Циферки'],
#         ['Заявленное количество мест говна', 'Что-то очень полезное', 'Циферки'],
#         ['Важный перец', 'Что-то очень полезное', 'Циферки'],
#         ['Номер-хуемер', 'Что-то очень полезное', 'Циферки'],
#         ['Важный перец', 'Что-то очень полезное', 'Циферки']
#     ], ['Какой-то ебаный заголовок номер один', 'Что-то очень полезное', 'Циферки'])
#     email.add_list([['Ваши документы'], ['Место на складе'], ['Наших водителей к работе с вами. Морально']],
#                    title='Мы готовим:')
#     email.add_list([['Ждите письма менеджера'], ['Очень терпеливо ждите'], ['Нет, звонок не поможет ускорить процесс'],
#                     ['Если все же вам хочется позвонить, сначала сходите нахер']], 'ol', title='Ваши следующие шаги:')
#     email.add_url(request.build_absolute_uri(), 'Смотреть на портале',
#                   'Чтобы увидеть подробности, перейдите по ссылке:')
#     msg = EmailMultiAlternatives(
#         subject='subject',
#         body=email.txt(),
#         from_email=settings.EMAIL_HOST_USER,
#         to=[settings.EMAIL_HOST_USER]
#     )
#     msg.mixed_subtype = 'related'
#     msg.attach_alternative(email.html(), "text/html")
#     for img in email.images:
#         msg.attach(img)
#
#     try:
#         result = msg.send(fail_silently=False)
#         messages.success(request, result)
#     except Exception as e:
#         messages.error(request, e)
#     return redirect(request.META.get('REFERER', '/'))
