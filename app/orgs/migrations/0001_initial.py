# Generated by Django 4.2.11 on 2024-03-30 19:41

import cats.models
from django.db import migrations, models
import django.db.models.deletion
import orgs.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cats', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('last_update', models.DateTimeField(auto_now=True, verbose_name='Время последнего изменения')),
                ('inn', models.CharField(blank=True, db_index=True, max_length=12, null=True, validators=[orgs.validators.NumericStringValidator('ИНН', [10, 12])], verbose_name='ИНН')),
                ('kpp', models.CharField(blank=True, db_index=True, max_length=9, null=True, validators=[orgs.validators.NumericStringValidator('КПП', [9])], verbose_name='КПП')),
                ('ogrn', models.CharField(blank=True, db_index=True, max_length=15, null=True, validators=[orgs.validators.NumericStringValidator('ОГРН', [13, 15])], verbose_name='ОГРН')),
                ('name', models.CharField(db_index=True, max_length=255, verbose_name='Отображаемое имя')),
                ('legal_name', models.CharField(db_index=True, max_length=255, verbose_name='Юр. наименование')),
                ('legal_address', models.CharField(max_length=255, verbose_name='Юр. адрес')),
                ('fact_address', models.CharField(max_length=255, verbose_name='Факт. адрес')),
                ('is_client', models.BooleanField(default=False, verbose_name='Является заказчиком')),
                ('is_expeditor', models.BooleanField(default=False, editable=False, verbose_name='Является экспедитором')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email')),
            ],
            options={
                'verbose_name': 'организация',
                'verbose_name_plural': 'организации',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('last_update', models.DateTimeField(auto_now=True, verbose_name='Время последнего изменения')),
                ('number', models.CharField(db_index=True, max_length=50, verbose_name='Номер договора')),
                ('date', models.DateField(verbose_name='Дата договора')),
                ('expiry_date', models.DateField(blank=True, null=True, verbose_name='Дата окончания действия')),
                ('currency', models.ForeignKey(default=cats.models.Currency.get_default_pk, on_delete=django.db.models.deletion.PROTECT, to='cats.currency', verbose_name='Валюта')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orgs.organisation', verbose_name='Контрагент')),
            ],
            options={
                'verbose_name': 'договор',
                'verbose_name_plural': 'договоры',
                'ordering': ('date', 'number'),
                'unique_together': {('organization', 'number')},
            },
        ),
    ]
