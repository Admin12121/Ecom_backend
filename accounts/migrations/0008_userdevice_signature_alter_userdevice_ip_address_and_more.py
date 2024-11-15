# Generated by Django 4.2.11 on 2024-07-21 09:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_delete_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdevice",
            name="signature",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="userdevice",
            name="ip_address",
            field=models.GenericIPAddressField(null=True),
        ),
        migrations.CreateModel(
            name="SiteViewLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
