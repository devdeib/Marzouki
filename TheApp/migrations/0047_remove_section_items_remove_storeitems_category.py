# Generated by Django 5.0.2 on 2024-05-27 11:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0046_remove_section_items_remove_storeitems_category_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='section',
            name='items',
        ),
        migrations.RemoveField(
            model_name='storeitems',
            name='category',
        ),
    ]
