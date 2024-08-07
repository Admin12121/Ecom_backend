from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutViewSet, LayoutSectionViewSet, ImageViewSet

router = DefaultRouter()
router.register(r'layouts', LayoutViewSet)
router.register(r'layout-sections', LayoutSectionViewSet)
router.register(r'images', ImageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]