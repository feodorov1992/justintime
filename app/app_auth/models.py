import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as DjangoGroup
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import AbstractModel
from orgs.models import Organisation


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
        if self.organization.is_expeditor:
            self.is_staff = True
        else:
            self.is_staff = False
        if self.is_staff:
            self.main_manager = None
        if self.username and not self.email:
            self.email = self.username
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = 'last_name',


@receiver(post_save, sender=User)
def save_order(sender, instance: User, created, **kwargs):
    if created:
        print(instance)


class Group(DjangoGroup):

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'
        proxy = True
