# Generated by Django 5.0.2 on 2024-06-09 15:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0054_remove_itemvariation_price_increase_percentage_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='choices',
            name='price_increment',
        ),
    ]
