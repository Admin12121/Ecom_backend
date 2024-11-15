# Generated by Django 4.2.11 on 2024-07-22 06:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_alter_siteviewlog_enclg_alter_userdevice_signature"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siteviewlog",
            name="city",
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="siteviewlog",
            name="country",
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name="siteviewlog",
            name="region",
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name="siteviewlog",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="siteviewlog",
            name="user_agent",
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
