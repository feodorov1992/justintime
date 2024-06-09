from time import sleep

from django.apps import apps
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.defaultfilters import safe
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from app.celery import app
from core.mailer import MailNotification
from orgs.models import Organisation


def get_confirm_url(user):
    user_pk = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    return reverse('registration_confirm', kwargs={'uidb64': user_pk, 'token': token})


@app.task
def user_confirm(user_pk, asleep=True):
    if asleep:
        sleep(1)
    user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
    expeditor = Organisation.objects.get(is_expeditor=True)

    subject = 'Just In Time - Подтверждение регистрации'
    email = MailNotification(subject, subject)
    text_lines = [
        f'Уважаемый(-ая) <b>{user}</b>!',
        f'Вы были зарегистрированы на портале <b>{expeditor}</b>.',
    ]
    text = safe('<br>'.join(text_lines))
    email.add_text(text)
    email.add_inner_link(get_confirm_url(user),
                         'Завершить регистрацию',
                         'Для завершения регистрации перейдите по ссылке:')
    email.add_recipients(user.email)
    email.send()


@app.task
def user_confirm_mass(user_pks):
    sleep(1)
    for pk in user_pks:
        user_confirm.delay(pk, asleep=False)


@app.task
def password_restore(user_pk):
    sleep(1)
    user = apps.get_model('app_auth', 'User').objects.get(pk=user_pk)
    expeditor = Organisation.objects.get(is_expeditor=True)

    subject = 'Just In Time - Восстановление пароля'
    email = MailNotification(subject, subject)
    text_lines = [
        f'Уважаемый(-ая) <b>{user}</b>!',
        f'Мы получили запрос на восстановление пароля от учетной записи',
        f'на портале <b>{expeditor}</b>.',
    ]
    text = safe('<br>'.join(text_lines))
    email.add_text(text)
    email.add_inner_link(get_confirm_url(user),
                         'Восстановить пароль',
                         'Для восстановления пароля перейдите по ссылке:')
    email.add_recipients(user.email)
    email.send()
