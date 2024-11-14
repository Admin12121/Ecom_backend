from django.contrib import admin
from .models import *
# Register your models here.
class Redeem_CodeAdmin(admin.ModelAdmin):
    list_display = ('name' ,'code' , 'discount', 'limit', 'used', 'is_active')
    search_fields = ('name', 'code')

class Saled_ProdInline(admin.TabularInline):
    model = Saled_Products  # Add () to indicate it's a class
    extra = 1

class SalesAdmin(admin.ModelAdmin):
    inlines = [Saled_ProdInline]
    list_display = ('costumer_name' ,'transactionuid' , 'grand_total', 'status')
    search_fields = ('costumer_name','status', 'transactionuid')



admin.site.register(Sales,SalesAdmin)
admin.site.register(Saled_Products)
admin.site.register(Redeem_Code, Redeem_CodeAdmin)

