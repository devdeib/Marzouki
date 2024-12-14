# Generated by Django 5.0.2 on 2024-11-01 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0071_alter_storeitems_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choices',
            name='price_increment',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True),
        ),
    ]