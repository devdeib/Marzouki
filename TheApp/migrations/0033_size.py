# Generated by Django 5.0.2 on 2024-05-23 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0032_storeitems_variations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
    ]
