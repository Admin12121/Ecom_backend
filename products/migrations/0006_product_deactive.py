# Generated by Django 4.2.11 on 2024-12-14 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_review_favoutare'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='deactive',
            field=models.BooleanField(default=False),
        ),
    ]