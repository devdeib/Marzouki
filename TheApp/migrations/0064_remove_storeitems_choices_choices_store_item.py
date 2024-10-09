# Generated by Django 5.0.2 on 2024-10-04 16:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0063_storeitems_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storeitems',
            name='choices',
        ),
        migrations.AddField(
            model_name='choices',
            name='store_item',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='TheApp.storeitems'),
        ),
    ]
