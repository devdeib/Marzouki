# Generated by Django 4.2.7 on 2024-02-12 16:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_alter_storeitems_item_photo'),
    ]

    operations = [
        migrations.DeleteModel(
            name='StoreItems',
        ),
    ]
