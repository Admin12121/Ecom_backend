from django.urls import path
from .views import *


urlpatterns = [
    path('sales/', SalesDataView.as_view(), name='sales'),
    path('cart/', AddToCartView.as_view(), name='cart'),
    path('redeemcode/', Redeem_CodeView.as_view(), name='redeem-code'),
]
