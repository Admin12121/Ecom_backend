# Generated by Django 4.2.11 on 2024-11-19 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='index',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
