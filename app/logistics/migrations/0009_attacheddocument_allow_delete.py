# Generated by Django 4.2.11 on 2024-06-06 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0008_alter_cargo_height_alter_cargo_length_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attacheddocument',
            name='allow_delete',
            field=models.BooleanField(default=False, verbose_name='Клиент может удалить'),
        ),
    ]
