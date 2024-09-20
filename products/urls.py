from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SubcategoryViewSet, ProductViewSet, ProductVariantViewSet,
    ProductImageViewSet, ReviewViewSet, CommentViewSet, CommentReplyViewSet,
    TrendingView, RecommendationView, NotifyUserViewSet, AddToCartViewSet, ReviewPostViewSet
    )

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'subcategories', SubcategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-variants', ProductVariantViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'reviews/(?P<product_slug>[^/.]+)/data', ReviewViewSet)
router.register(r'reviews/post', ReviewPostViewSet, basename='review-post')
router.register(r'comments', CommentViewSet)
router.register(r'comment-replies', CommentReplyViewSet)
router.register(r'notifyuser', NotifyUserViewSet)
router.register(r'cart', AddToCartViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('trending/', TrendingView.as_view(), name='trending'),
    path("reviews/", ReviewViewSet.as_view({'get': 'list'}), name='admin-reviews'),
    path('recommendations/', RecommendationView.as_view(), name='recommendations'),
    path('get_products_by_ids/', ProductViewSet.as_view({'get': 'get_products_by_ids'}), name='get-products-by-ids'), 
]
