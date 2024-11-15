# Generated by Django 4.2.11 on 2024-07-25 18:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_alter_siteviewlog_user_deliveryaddress"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.CharField(
                blank=True,
                choices=[("Admin", "admin"), ("Staff", "staff"), ("User", "user")],
                default="User",
                max_length=20,
                null=True,
            ),
        ),
    ]
