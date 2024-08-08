from django.db import models
from products.utils import validate_image_format, compress_image, generate_slug , generate_unique_slug
# Create your models here.
class Layout(models.Model):
    name = models.CharField(max_length=255)
    layout_slug = models.CharField(max_length=255)
    non_deletable = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if not self.layout_slug:
            self.layout_slug = generate_unique_slug(self.name)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
    
class LayoutSection(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE)
    code = models.TextField()
    def __str__(self):
        return self.name
    
class Image(models.Model):
    layout_section = models.ForeignKey(LayoutSection, on_delete=models.CASCADE)
    image_id = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images/')
    def __str__(self):
        return self.name