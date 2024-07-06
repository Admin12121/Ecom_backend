from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SubcategoryViewSet, ProductViewSet, ProductVariantViewSet,
    ProductImageViewSet, ReviewViewSet, CommentViewSet, CommentReplyViewSet,
    TrendingView, RecommendationView,CategoryView
    )

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'subcategories', SubcategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-variants', ProductVariantViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'comment-replies', CommentReplyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('post/', CategoryView.as_view(), name='post'),
    path('trending/', TrendingView.as_view(), name='trending'),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
]
