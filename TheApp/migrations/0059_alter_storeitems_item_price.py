# Generated by Django 5.0.2 on 2024-06-13 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0058_alter_storeitems_item_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storeitems',
            name='item_price',
            field=models.FloatField(),
        ),
    ]