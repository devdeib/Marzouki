# Generated by Django 5.0.2 on 2024-06-07 22:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0051_alter_section_items'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ItemImage',
            new_name='StoreItemImage',
        ),
    ]
