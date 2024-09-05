from django.db import models
from products.utils import validate_image_format, compress_image, generate_slug , generate_unique_slug
# Create your models here.
class Layout(models.Model):
    name = models.CharField(max_length=255)
    layout_slug = models.CharField(max_length=255, null=True, blank=True)
    non_deletable = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    no_image = models.IntegerField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.layout_slug:
            self.layout_slug = generate_slug(self.name)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name
    
class Image(models.Model):
    layout = models.ForeignKey(Layout, on_delete=models.CASCADE)
    image_id = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images/')
    link_no = models.IntegerField(null=True, blank=True)
    title_no = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return self.layout.name
    
class Link(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    link = models.URLField(max_length=250, null=True, blank=True)

class Title(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    title = models.CharField(max_length=250, null=True, blank=True)
