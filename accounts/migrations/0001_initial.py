# Generated by Django 4.2.11 on 2024-11-14 19:25

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('first_name', models.CharField(blank=True, max_length=200)),
                ('last_name', models.CharField(blank=True, max_length=200)),
                ('username', models.CharField(blank=True, max_length=200, null=True, unique=True)),
                ('email', models.EmailField(max_length=255, unique=True, verbose_name='Email')),
                ('profile', models.ImageField(blank=True, null=True, upload_to='profile/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('dob', models.CharField(blank=True, max_length=10, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
                ('role', models.CharField(blank=True, choices=[('Admin', 'admin'), ('Staff', 'staff'), ('User', 'user')], default='User', max_length=20, null=True)),
                ('state', models.CharField(choices=[('inactive', 'Inactive'), ('active', 'Active'), ('blocked', 'Blocked')], default='inactive', max_length=20)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('otp_token', models.CharField(blank=True, max_length=6, null=True)),
                ('otp_created_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_type', models.CharField(max_length=50)),
                ('device_os', models.CharField(max_length=50)),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now)),
                ('ip_address', models.GenericIPAddressField(null=True)),
                ('signature', models.CharField(max_length=200, null=True, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SiteViewLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(db_index=True, max_length=255)),
                ('country', models.CharField(db_index=True, max_length=100)),
                ('city', models.CharField(db_index=True, max_length=200)),
                ('region', models.CharField(db_index=True, max_length=200)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('encsh', models.CharField(max_length=200)),
                ('enclg', models.CharField(max_length=200)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='site_view_logs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=255)),
                ('search_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='search_history', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
                ('mobile_number', models.CharField(max_length=255)),
                ('provience', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('area', models.CharField(max_length=255)),
                ('default_delivery_addresh', models.BooleanField(default=False)),
                ('default_billing_address', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_address', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=255)),
                ('providerId', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'accounts',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['id', 'email', 'username'], name='accounts_us_id_f4dbe7_idx'),
        ),
    ]
