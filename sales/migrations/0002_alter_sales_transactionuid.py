# Generated by Django 4.2.11 on 2024-11-29 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sales',
            name='transactionuid',
            field=models.CharField(blank=True, max_length=225, null=True),
        ),
    ]