from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'admin-users', AdminUserViewSet, basename='admin-users') 
router.register(r'search', SearchView, basename='search') 
router.register(r'site-view-logs', SiteViewLogViewSet, basename='site-view-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('reset_password/', PasswordResetView.as_view(), name='reset_password/'),
    path('activate/<str:uidb64>/<str:token>/', UserActivationView.as_view() , name='activate'),    
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
