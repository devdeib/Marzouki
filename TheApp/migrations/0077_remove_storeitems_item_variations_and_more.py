# Generated by Django 5.0.2 on 2024-11-07 20:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0076_alter_itemvariation_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storeitems',
            name='item_variations',
        ),
        migrations.AlterField(
            model_name='itemvariation',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_variations', to='TheApp.storeitems'),
        ),
    ]
