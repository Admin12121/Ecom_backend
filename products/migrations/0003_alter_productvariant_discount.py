# Generated by Django 4.2.11 on 2024-11-20 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_productimage_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productvariant',
            name='discount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
