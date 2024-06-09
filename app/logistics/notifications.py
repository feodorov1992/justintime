from django.apps import apps
from django.urls import reverse

from app.celery import app
from core.mailer import MailNotification


@app.task
def order_update_client_notification(order_pk, user_pk, changes):
    order = apps.get_model('logistics', 'Order').objects.get(pk=order_pk)
    user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
    client_number = changes.get("client_number", {}).get("old", order.client_number) or order.number
    exclude = 'service_marks',

    email = MailNotification(
        f'Заявка № {client_number} изменена',
        f'Заявка изменена<br><u>{client_number}</u>'
    )

    for field_name in exclude:
        if field_name in changes:
            changes.pop(field_name)

    if changes:
        email.add_list([['Автор изменений', str(user)]])
        email.add_table(order.humanize_changes(changes, flat=True), ['Наименование поля', 'Было', 'Стало'])
        email.add_inner_link(
            reverse('order_detail', kwargs={'pk': order_pk}),
            'Смотреть на портале',
            'Чтобы увидеть подробности, перейдите по ссылке:'
        )

        if order.client_employee:
            recipients = [order.client_employee.email]
        elif order.client.email:
            recipients = [order.client.email]
        else:
            recipients = order.client.user_set.filter(email__isnull=False).values_list('email', flat=True)

        email.add_recipients(*recipients)
        email.send()


@app.task
def order_update_manager_notification(order_pk, user_pk, changes):

    if changes:
        order = apps.get_model('logistics', 'Order').objects.get(pk=order_pk)
        user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
        number = changes.get("number", {}).get("old", order.number)
        client_number = changes.get("client_number", {}).get("old", order.client_number) or order.number
        subject = f'Заявка № {number} изменена'

        email = MailNotification(
            f'Заявка № {number} изменена',
            f'{subject}<br><u>{client_number}</u>' if client_number != number else subject
        )

        email.add_list([['Автор изменений', str(user)]])
        email.add_table(order.humanize_changes(changes, flat=True), ['Наименование поля', 'Было', 'Стало'])
        email.add_inner_link(
            reverse('admin:logistics_order_change', args=[order_pk]),
            'Смотреть в админке',
            'Чтобы увидеть подробности, перейдите по ссылке:'
        )

        if order.manager:
            recipients = [order.manager.email]
        elif user.main_manager and user.main_manager.email:
            recipients = [order.main_manager.email]
        else:
            expeditor = apps.get_model('orgs', 'Organisation').objects.get(is_expeditor=True)
            if expeditor.email:
                recipients = [expeditor.email]
            else:
                recipients = expeditor.user_set.filter(email__isnull=False).values_list('email', flat=True)

        email.add_recipients(*recipients)
        email.send()
