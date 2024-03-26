import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task
def send_test_email():
    from django.core.mail import send_mail
    return send_mail(
        "Subject here",
        "Here is the message.",
        "feodorov1992@mail.ru",
        ["feodorov1992@gmail.com"],
        fail_silently=False,
    )
