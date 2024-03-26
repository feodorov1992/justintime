from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models

from app.models import AbstractModel
from cats.models import Organisation


class User(AbstractModel, AbstractUser):
    username = models.EmailField(verbose_name='Логин (Email)', unique=True,
                                 error_messages={"unique": "Такой пользователь уже существует!"})
    last_name = models.CharField('Фамилия', max_length=150)
    first_name = models.CharField('Имя', max_length=150)
    second_name = models.CharField('Отчество', max_length=150, blank=True)
    email = models.EmailField(verbose_name='Email', blank=True, editable=False)
    main_manager = models.ForeignKey('self', verbose_name='Основной менеджер', on_delete=models.SET_NULL,
                                     blank=True, null=True)
    organization = models.ForeignKey(Organisation, verbose_name='Организация', on_delete=models.CASCADE)

    def get_full_name(self):
        name_list = [self.last_name, self.first_name]
        if self.second_name:
            name_list.append(self.second_name)
        return ' '.join([word.strip().capitalize() for word in name_list])

    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name.strip() else self.username

    def save(self, *args, **kwargs):
        if self.organization_id is None and (self.is_staff or self.is_superuser):
            self.organization = Organisation.objects.get(is_expeditor=True)
        if self.username and not self.email:
            self.email = self.username
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'


class Group(DjangoGroup):
    """Instead of trying to get new user under existing `Aunthentication and Authorization`
    banner, create a proxy group model under our Accounts app label.
    Refer to: https://github.com/tmm/django-username-email/blob/master/cuser/admin.py
    """

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'
        proxy = True
