# Generated by Django 4.2.7 on 2024-02-24 14:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TheApp', '0005_storeitems_item_quantity_storeitems_item_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='storeitems',
            name='item_size',
        ),
        migrations.CreateModel(
            name='ItemSize',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price_increase_percentage', models.DecimalField(decimal_places=2, max_digits=5)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TheApp.storeitems')),
                ('size', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TheApp.size')),
            ],
        ),
        migrations.AddField(
            model_name='storeitems',
            name='sizes',
            field=models.ManyToManyField(through='TheApp.ItemSize', to='TheApp.size'),
        ),
    ]
