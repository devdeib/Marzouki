# Generated by Django 5.0.2 on 2024-10-04 23:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0064_remove_storeitems_choices_choices_store_item'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='choices',
            name='store_item',
        ),
        migrations.AddField(
            model_name='choices',
            name='item',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='TheApp.storeitems'),
        ),
        migrations.AddField(
            model_name='storeitems',
            name='item_choices',
            field=models.CharField(blank=True, default=None, max_length=200, null=True, verbose_name='Choices'),
        ),
    ]
