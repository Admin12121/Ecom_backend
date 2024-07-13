from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, GoogleLogin
from .otp_views import OTPViewSet 
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'otp', OTPViewSet, basename='otp')  # add this line

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),  # Ensure allauth URLs are included    
    path('dj-rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
]
