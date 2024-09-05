from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LayoutViewSet

router = DefaultRouter()
# router.register(r'layouts', LayoutViewSet)

urlpatterns = [
    path('layouts/<slug:layout_slug>/image/<slug:id>/', LayoutViewSet.as_view({
        'patch': 'update_image'
    }), name='layout-update-image'),
    path('layouts/<slug:layout_slug>/title/<slug:id>/', LayoutViewSet.as_view({
        'patch': 'update_title'
    }), name='layout-update-title'),
    path('layouts/<slug:layout_slug>/link/<slug:id>/', LayoutViewSet.as_view({
        'patch': 'update_link'
    }), name='layout-update-link'),    
    path('layouts/<slug:layout_slug>/activate/<slug:id>/', LayoutViewSet.as_view({
        'patch': 'activate'
    }), name='activate'),    
    path('layouts/<slug:layout_slug>/', LayoutViewSet.as_view({
        'get': 'retrieve',
        'patch': 'update',
        'delete': 'destroy'
    }), name='layout-detail'),
    path('layouts/', LayoutViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='layout-list'),
]