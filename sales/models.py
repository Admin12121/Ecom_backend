from django.db import models
from accounts.models import User, DeliveryAddress
from products.models import Product, ProductVariant
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class Redeem_Code(models.Model):
   name = models.CharField(max_length=100, null=True, blank=True)
   code = models.CharField(max_length=100,unique=True,null=True, blank=True)
   type = models.CharField(max_length=10, choices=[('amount', 'Amount'), ('percentage', 'Percentage')], null=True, blank=True)
   discount = models.IntegerField(null=True, blank=True)
   minimum = models.IntegerField(null=True, blank=True)
   limit = models.IntegerField(null=True, blank=True)
   used = models.IntegerField(null=True, blank=True, default=0)
   valid_until = models.DateField(null=True, blank=True)
   is_active = models.BooleanField(null=True, blank=True)

#    def __str__(self):
#       return self.name


class Sales(models.Model):
    costumer_name = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None)
    transactionuid = models.CharField(max_length=225, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('proceed', 'Proceed'),
            ('packed', 'Packed'),
            ('delivered', 'Delivered'),
            ('successful', 'Successful'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
    )
    total_amt = models.FloatField()
    sub_total = models.FloatField()
    shipping = models.ForeignKey(DeliveryAddress, on_delete=models.SET_DEFAULT, null=True,blank=True, default=None)
    discount = models.FloatField(null=True, blank=True)
    payment_method = models.CharField(max_length=100,null=True,blank=True)
    redeem_data = models.CharField(max_length=100,null=True,blank=True)
    payment_intent_id = models.CharField(max_length=100,null=True,blank=True)
    created = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    def __str__(self):
      return f"{self.costumer_name}"


class Saled_Products(models.Model): 
   transition = models.ForeignKey(Sales, on_delete=models.CASCADE, null=True, blank=True,related_name='products')
   product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT, null=True, default=None)
   variant = models.ForeignKey(ProductVariant,on_delete=models.SET_DEFAULT,null=True, default=None)
   price = models.FloatField()
   qty = models.FloatField()
   total = models.FloatField()
    
   def __str__(self):
     return f"{self.product}"