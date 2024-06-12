from time import sleep

from django.apps import apps
from django.urls import reverse

from app.celery import app
from core.mailer import MailNotification


def get_clients_recipients_from_order(order):
    if order.client_employee:
        return [order.client_employee.email]
    elif order.client.email:
        return [order.client.email]
    return order.client.user_set.filter(email__isnull=False).values_list('email', flat=True)


def get_managers_recipients_from_order(order, user):
    if order.manager:
        return [order.manager.email]
    elif user.main_manager and user.main_manager.email:
        return [user.main_manager.email]
    expeditor = apps.get_model('orgs', 'Organisation').objects.get(is_expeditor=True)
    if expeditor.email:
        return [expeditor.email]
    return expeditor.user_set.filter(email__isnull=False).values_list('email', flat=True)


@app.task
def order_update_client_notification(order_pk, user_pk, changes):
    sleep(1)
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

        email.add_recipients(*get_clients_recipients_from_order(order))
        email.send()


@app.task
def order_update_manager_notification(order_pk, user_pk, changes):
    sleep(1)
    if changes:
        order = apps.get_model('logistics', 'Order').objects.get(pk=order_pk)
        user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
        number = changes.get("number", {}).get("old", order.number)
        client_number = changes.get("client_number", {}).get("old", order.client_number) or order.number
        subject = f'Заявка № {number} изменена'

        email = MailNotification(
            subject, f'{subject}<br><u>{client_number}</u>' if client_number != number else subject
        )

        email.add_list([['Автор изменений', str(user)]])
        email.add_table(order.humanize_changes(changes, flat=True), ['Наименование поля', 'Было', 'Стало'])
        email.add_inner_link(
            reverse('admin:logistics_order_change', args=[order_pk]),
            'Смотреть в админке',
            'Чтобы увидеть подробности, перейдите по ссылке:'
        )

        email.add_recipients(*get_managers_recipients_from_order(order, user))
        email.send()


@app.task
def order_create_client_notification(order_pk, user_pk):
    sleep(1)
    order = apps.get_model('logistics', 'Order').objects.get(pk=order_pk)
    user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
    subject = f'Создана заявка № {order.number}'
    email = MailNotification(subject, subject)

    list_items = [['Клиентский номер', order.client_number]] if order.client_number else list()
    list_items.append(['Создатель заявки', str(user)])
    if order.manager:
        list_items.append(['Менеджер', str(order.manager)])

    email.add_list(list_items)
    email.add_inner_link(
        reverse('order_detail', kwargs={'pk': order_pk}),
        'Смотреть на портале',
        'Чтобы увидеть подробности, перейдите по ссылке:'
    )

    email.add_recipients(*get_clients_recipients_from_order(order))
    email.send()


@app.task
def order_create_manager_notification(order_pk, user_pk):
    sleep(1)
    order = apps.get_model('logistics', 'Order').objects.get(pk=order_pk)
    user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
    subject = f'Создана заявка № {order.number}'
    email = MailNotification(subject, subject)

    list_items = [
        ['Создатель заявки', str(user)],
        ['Заказчик', str(order.client)]
    ]
    if order.client_number:
        list_items.append(['Клиентский номер', order.client_number])
    if order.client_employee:
        list_items.append(['Наблюдатель', str(order.client_employee)])

    email.add_list(list_items)
    email.add_inner_link(
        reverse('admin:logistics_order_change', args=[order_pk]),
        'Смотреть в админке',
        'Чтобы увидеть подробности, перейдите по ссылке:'
    )

    email.add_recipients(*get_managers_recipients_from_order(order, user))
    email.send()


@app.task
def quick_order_create_manager_notification(order_pk):
    sleep(1)
    quick_order = apps.get_model('logistics', 'QuickOrder').objects.get(pk=order_pk)
    user = quick_order.created_by
    subject = f'Создана быстрая заявка № {quick_order.number}'
    email = MailNotification(subject, subject)

    list_items = [
        ['Создатель заявки', str(user)],
        ['Заказчик', str(quick_order.client)]
    ]
    if quick_order.client_number:
        list_items.append(['Клиентский номер', quick_order.client_number])

    email.add_list(list_items)
    email.add_inner_link(
        reverse('admin:logistics_quickorder_change', args=[order_pk]),
        'Смотреть в админке',
        'Чтобы увидеть подробности, перейдите по ссылке:'
    )
    expeditor = apps.get_model('orgs', 'Organisation').objects.get(is_expeditor=True)
    if user.main_manager and user.main_manager.email:
        recipients = [user.main_manager.email]
    elif expeditor.email:
        recipients = [expeditor.email]
    else:
        recipients = expeditor.user_set.filter(email__isnull=False).values_list('email', flat=True)

    email.add_recipients(*recipients)
    email.send()
