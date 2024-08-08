from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutViewSet

router = DefaultRouter()
router.register(r'layouts', LayoutViewSet)

urlpatterns = [
    path('', include(router.urls)),
]