# Generated by Django 4.2.11 on 2024-03-31 13:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0004_alter_orderstatus_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='status',
        ),
    ]
