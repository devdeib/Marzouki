# Generated by Django 4.2.7 on 2024-02-24 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0004_remove_cart_quantity_delete_wishlist'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeitems',
            name='item_quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='storeitems',
            name='item_size',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
