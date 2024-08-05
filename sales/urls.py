from django.urls import path
from .views import *


urlpatterns = [
    path('sales/', SalesDataView.as_view(), name='sales'),
    path('redeemcode/', Redeem_CodeView.as_view(), name='redeem-code'),
]
