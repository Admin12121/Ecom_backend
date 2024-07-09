from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from .otp_views import OTPViewSet 
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'otp', OTPViewSet, basename='otp')  # add this line


urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
