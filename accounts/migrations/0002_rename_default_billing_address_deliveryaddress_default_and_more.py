# Generated by Django 4.2.11 on 2024-11-28 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deliveryaddress',
            old_name='default_billing_address',
            new_name='default',
        ),
        migrations.AddField(
            model_name='deliveryaddress',
            name='country',
            field=models.CharField(default=1, max_length=225),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='deliveryaddress',
            name='zipcode',
            field=models.CharField(default=12, max_length=225),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='deliveryaddress',
            name='address',
            field=models.CharField(max_length=225),
        ),
        migrations.AlterField(
            model_name='deliveryaddress',
            name='city',
            field=models.CharField(max_length=225),
        ),
        migrations.AlterUniqueTogether(
            name='deliveryaddress',
            unique_together={('user', 'default')},
        ),
        migrations.RemoveField(
            model_name='deliveryaddress',
            name='area',
        ),
        migrations.RemoveField(
            model_name='deliveryaddress',
            name='default_delivery_addresh',
        ),
        migrations.RemoveField(
            model_name='deliveryaddress',
            name='mobile_number',
        ),
        migrations.RemoveField(
            model_name='deliveryaddress',
            name='name',
        ),
        migrations.RemoveField(
            model_name='deliveryaddress',
            name='provience',
        ),
    ]