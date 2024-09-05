from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutViewSet

router = DefaultRouter()
# router.register(r'layouts', LayoutViewSet)

urlpatterns = [
    path('layouts/', LayoutViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='layout-list'),
    path('layouts/<slug:layout_slug>/', LayoutViewSet.as_view({
        'get': 'retrieve',
        'patch': 'update',
        'delete': 'destroy'
    }), name='layout-detail'),
]