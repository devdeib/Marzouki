# Generated by Django 5.0.2 on 2024-05-27 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0038_alter_storeitems_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storeitems',
            name='category',
        ),
    ]
