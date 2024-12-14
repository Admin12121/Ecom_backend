from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from .utils import validate_image_format, compress_image, generate_slug , generate_unique_slug
from accounts.models import User
import os

class Category(models.Model):
    name = models.CharField(max_length=255,unique=True)
    categoryslug = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='category_images/', validators=[validate_image_format], null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.categoryslug:
            self.categoryslug = generate_slug(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    deactive = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    productslug = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.productslug:
            self.productslug = generate_unique_slug(self.product_name, Product)
        super().save(*args, **kwargs)
        
    class Meta:
        indexes = [
            models.Index(fields=['id', 'product_name', 'productslug']),
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
        ]

    def get_average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return None

    def get_total_ratings(self):
        return self.reviews.count()

    def __str__(self):
        return self.product_name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_stripe_id = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.IntegerField(null=True, blank=True)
    stock = models.PositiveIntegerField()

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.product_name} - {self.size or 'Single'}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    index = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='product_images/', validators=[validate_image_format])

    def delete(self, *args, **kwargs):
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.product.images.count() >= 5:
            raise ValidationError('You can only upload a maximum of 5 images per product.')
                
        if self.image:
            self.image = compress_image(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} Image"

class NotifyUser(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='notify_user', null=True, blank=True)
    variant = models.SmallIntegerField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(null=True,blank=True)

    def __str__(self):
        return f"{self.product.product_name} {self.email}"


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=255)
    content = models.TextField()
    recommended = models.BooleanField(default=True)
    delivery = models.BooleanField(default=True)
    favoutare = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.product.product_name} - {self.rating}'

class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="review_images", null=True, blank=True)
    image = models.ImageField(upload_to="review/image/", null=True, validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    def save(self, *args, **kwargs):
        if self.image:
            format = 'PNG' if self.image.name.lower().endswith('png') else 'JPEG'
            self.image = compress_image(self.image, format=format, quality=85)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.review}"

class Comment(models.Model):
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.product.product_name}'

class CommentReply(models.Model):
    comment = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - Reply to {self.comment.id}'

class AddtoCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_user')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='cart_product')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='cart_product_variant')
    pcs = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pcs > self.variant.stock:
            raise ValidationError('Not enough stock available')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product}"

    class Meta:
        unique_together = ('user', 'variant')