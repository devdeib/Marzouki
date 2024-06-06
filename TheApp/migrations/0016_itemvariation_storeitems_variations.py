# Generated by Django 5.0.2 on 2024-03-09 13:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0015_remove_storeitems_variations'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemVariation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variation_price', models.BigIntegerField(default=None)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TheApp.storeitems')),
                ('variation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TheApp.variation')),
            ],
        ),
        migrations.AddField(
            model_name='storeitems',
            name='variations',
            field=models.ManyToManyField(through='TheApp.ItemVariation', to='TheApp.variation'),
        ),
    ]
