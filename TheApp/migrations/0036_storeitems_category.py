# Generated by Django 5.0.2 on 2024-05-27 10:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0035_remove_storeitems_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeitems',
            name='category',
            field=models.ForeignKey(default='All Products', on_delete=django.db.models.deletion.CASCADE, related_name='items_category', to='TheApp.section'),
        ),
    ]
