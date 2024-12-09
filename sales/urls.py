from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalesViewSet, RedeemCodeViewSet

router = DefaultRouter()
router.register(r'sales', SalesViewSet, basename='sales')
router.register(r'redeemcode', RedeemCodeViewSet, basename='redeem-code')

urlpatterns = [
    path('', include(router.urls)),
    path('sales/transaction/<str:transactionuid>/', SalesViewSet.as_view({'get': 'retrieve'}), name='sales-detail'),
]