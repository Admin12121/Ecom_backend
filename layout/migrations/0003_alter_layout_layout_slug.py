# Generated by Django 4.2.11 on 2024-08-08 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layout', '0002_layout_layout_slug_alter_layout_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layout',
            name='layout_slug',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
