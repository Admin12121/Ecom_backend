from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import FileExtensionValidator
from django.utils.crypto import get_random_string
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
import sys
from django.core.exceptions import ValidationError

def compress_image(image, format='PNG', quality=85):
    image_temporary = Image.open(image)
    image_temporary = image_temporary.convert('RGBA' if format == 'PNG' else 'RGB')
    output_io_stream = BytesIO()
    image_temporary.save(output_io_stream, format=format, optimize=True, quality=quality)
    output_io_stream.seek(0)
    image = InMemoryUploadedFile(output_io_stream, 'ImageField', "%s.%s" % (image.name.split('.')[0], format.lower()), 'image/%s' % format.lower(), sys.getsizeof(output_io_stream), None)
    return image

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone,  password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, first_name, last_name, phone, password, **extra_fields)

class User(AbstractBaseUser):
    ROLE_CHOICES = (
        ('Admin', 'admin'),
        ('Staff','staff'),
        ('User', 'user'),
    )
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=200, blank=True, null=True, unique=True)
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    profile = models.ImageField(upload_to='profile/', null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    phone = models.CharField(max_length=15, blank=True)
    dob = models.CharField(max_length=10, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    role = models.CharField(max_length=20,choices=ROLE_CHOICES, default="User", null=True, blank=True)
    
    STATE_CHOICES = (
        ('inactive', 'Inactive'),
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    )
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='inactive')

    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    otp_token = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    def save(self, *args, **kwargs):
        if not self.username:
            while True:
                random_string = get_random_string(length=6)
                potential_username = f"@{self.first_name}_{self.last_name}_{random_string}"
                if not User.objects.filter(username=potential_username).exists():
                    self.username = potential_username
                    break        
        if self.profile:
            format = 'PNG' if self.profile.name.lower().endswith('png') else 'JPEG'
            self.profile = compress_image(self.profile, format=format, quality=85)
        super(User, self).save(*args, **kwargs)
    class Meta:
        indexes = [
            models.Index(fields=['id', 'email', 'username']),
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

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    providerId = models.CharField(max_length=255)
    details = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'accounts'

class DeliveryAddress(models.Model):
    user = models.ForeignKey(User, related_name='delivery_addresses', on_delete=models.CASCADE)
    address = models.CharField(max_length=225)
    country = models.CharField(max_length=225)
    city = models.CharField(max_length=225)
    zipcode = models.CharField(max_length=225)
    default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'default'],
                condition=models.Q(default=True),
                name='unique_default_address_per_user'
            )
        ]

    def clean(self):
        if self.default:
            # Check if the user already has a default address
            default_exists = DeliveryAddress.objects.filter(user=self.user, default=True).exclude(pk=self.pk).exists()
            if default_exists:
                raise ValidationError("The user already has a default delivery address.")
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run the clean method before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.email if self.user else "No User"} - {self.address}'


class SearchHistory(models.Model):
    user = models.ForeignKey(User, related_name='search_history', on_delete=models.CASCADE, null=True, blank=True)
    keyword = models.CharField(max_length=255)
    search_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.email if self.user else "No User"} - {self.keyword}'

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
    ip_address = models.GenericIPAddressField(null=True)
    signature = models.CharField(max_length=200,null=True, unique=True)

    def __str__(self):
        return f'{self.user.email if self.user else "No User"} - {self.device_type} ({self.device_os})'

class SiteViewLog(models.Model):
    user = models.ForeignKey(User,related_name='site_view_logs', null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    city = models.CharField(max_length=200, db_index=True)
    region = models.CharField(max_length=200, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    encsh = models.CharField(max_length=200)
    enclg = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.user} - {self.timestamp}"