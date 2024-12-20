from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesViewSet, RedeemCodeViewSet, StripeWebhookView as webhook

router = DefaultRouter()
router.register(r'sales', SalesViewSet, basename='sales')
router.register(r'redeemcode', RedeemCodeViewSet, basename='redeem-code')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', webhook.as_view() , name='stripe-webhook'),
    path('sales/transaction/<str:transactionuid>/', SalesViewSet.as_view({'get': 'retrieve'}), name='sales-detail'),
]