# Generated by Django 5.0.2 on 2024-10-04 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0062_cart_item_alter_storeitems_item_variations'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeitems',
            name='choices',
            field=models.ManyToManyField(blank=True, default=True, to='TheApp.choices'),
        ),
    ]
