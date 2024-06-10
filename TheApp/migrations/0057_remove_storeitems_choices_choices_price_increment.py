# Generated by Django 5.0.2 on 2024-06-09 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0056_storeitems_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storeitems',
            name='choices',
        ),
        migrations.AddField(
            model_name='choices',
            name='price_increment',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
    ]