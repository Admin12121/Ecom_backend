from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from allauth.account.models import EmailAddress

def compress_image(image, format='PNG', quality=85):
    image_temporary = Image.open(image)
    image_temporary = image_temporary.convert('RGBA' if format == 'PNG' else 'RGB')
    output_io_stream = BytesIO()
    image_temporary.save(output_io_stream, format=format, optimize=True, quality=quality)
    output_io_stream.seek(0)
    image = InMemoryUploadedFile(output_io_stream, 'ImageField', "%s.%s" % (image.name.split('.')[0], format.lower()), 'image/%s' % format.lower(), sys.getsizeof(output_io_stream), None)
    return image

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone, tc, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, phone=phone, tc=tc, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone, tc, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, first_name, last_name, phone, tc, password, **extra_fields)

class User(AbstractBaseUser):
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    profile = models.ImageField(upload_to='profile/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=15, unique=True, blank=True)
    dob = models.CharField(max_length=10, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    otp_device = models.ForeignKey(TOTPDevice,related_name='otp_user', on_delete=models.SET_NULL, null=True, blank=True)
    is_otp_verified = models.BooleanField(default=False)
    tc = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone', 'tc']

    def save(self, *args, **kwargs):
        if self.profile:
            format = 'PNG' if self.profile.name.lower().endswith('png') else 'JPEG'
            self.profile = compress_image(self.profile, format=format, quality=85)
        super(User, self).save(*args, **kwargs)
    class Meta:
        indexes = [
            models.Index(fields=['id', 'email', 'first_name']),  # Index for id and year fields
        ]
    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def social_accounts(self):
        return EmailAddress.objects.filter(user=self)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(max_length=500, null=True, blank=True)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.email}'


class SearchHistory(models.Model):
    user = models.ForeignKey(User, related_name='search_history', on_delete=models.CASCADE)
    keyword = models.CharField(max_length=255)
    search_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.email} - {self.keyword}'

    def save(self, *args, **kwargs):
        user_search_history = SearchHistory.objects.filter(user=self.user)
        if user_search_history.count() >= 25:
            oldest_entries = user_search_history.order_by('search_date')[:user_search_history.count() - 24]
            oldest_entries.delete()
        super().save(*args, **kwargs)


class UserDevice(models.Model):
    user = models.ForeignKey(User, related_name='devices', on_delete=models.CASCADE)
    device_type = models.CharField(max_length=50)
    device_os = models.CharField(max_length=50)
    last_login = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f'{self.user.email} - {self.device_type} ({self.device_os})'
