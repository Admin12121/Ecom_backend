from django.db import models
from accounts.models import User
from products.models import Product
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Create your models here.
class Redeem_Code(models.Model):
   name = models.CharField(max_length=100, null=True, blank=True)
   code = models.CharField(max_length=100,unique=True,null=True, blank=True)
   type = models.BooleanField(null=True, blank=True)
   minimum = models.IntegerField(null=True, blank=True)
   discount = models.IntegerField(null=True, blank=True)
   limit = models.IntegerField(null=True, blank=True)
   maxamt = models.IntegerField(null=True, blank=True)
   used = models.IntegerField(null=True, blank=True)
   valid = models.DateField(null=True, blank=True)
   status = models.BooleanField(null=True, blank=True)

   def __str__(self):
      return self.name
   
@receiver(pre_save, sender=Redeem_Code)
def update_status(sender, instance, **kwargs):
    # Check if the code is still valid (valid date is after the current date)
    if instance.valid < timezone.now().date():
        instance.status = False
    # Check if the code has reached its usage limit
    elif instance.used >= instance.limit:
        instance.status = False
    else:
        instance.status = True


class Add_to_Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, related_name='cart_user')  # Unique related_name
    product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT, null=True, default=None)
    qty = models.FloatField()
    costumer_name = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, related_name='cart_costumer_name')  # Unique related_name

    def __str__(self):
        return f"{self.product}"


class Sales(models.Model):
    costumer_name = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None)
    transactionuid = models.IntegerField(null=True, blank=True)
    sub_total = models.FloatField()
    shipping = models.FloatField(null=True,blank=True)
    discount = models.FloatField(null=True, blank=True)
    status = models.BooleanField(null=True,blank=True)
    total_amt = models.FloatField()
    payment_method = models.CharField(max_length=100,null=True,blank=True)
    redeemCode= models.ForeignKey(Redeem_Code,on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    redeem_amt = models.FloatField(null=True, blank=True)
    grand_total = models.FloatField(null=True)
    created = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    def __str__(self):
      return f"{self.costumer_name}"


class Saled_Products(models.Model): 
   transition = models.ForeignKey(Sales, on_delete=models.CASCADE, null=True, blank=True,related_name='products')
   product = models.ForeignKey(Product, on_delete=models.SET_DEFAULT, null=True, default=None)
   product_name = models.CharField(max_length=100, null=True, blank=True)
   price = models.FloatField()
   qty = models.FloatField()
   total = models.FloatField()
    
   def __str__(self):
     return f"{self.product}"