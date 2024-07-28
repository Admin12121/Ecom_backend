from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, Comment, CommentReply, NotifyUser
from .serializers import (CategorySerializer, SubcategorySerializer, ProductSerializer,
                          ProductVariantSerializer, ProductImageSerializer, ReviewSerializer, CommentSerializer,
                          CommentReplySerializer, NotifyUserSerializer)
from accounts.models import User
from notification.models import Notification
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from collections import Counter
from accounts.models import (SearchHistory )
from rest_framework.permissions import IsAuthenticated , IsAuthenticatedOrReadOnly, AllowAny
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, SAFE_METHODS

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class CustomReadOnly(BasePermission):    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff

class CategoryView(APIView):
     def post(self, request, format=None):
        #    print(request.data)
           return Response({"Successfull"}, status=status.HTTP_200_OK)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('subcategory_set').all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.select_related('category').all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'subcategory').prefetch_related('productvariant_set', 'reviews', 'comments').all()
    serializer_class = ProductSerializer
    permission_classes = [CustomReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination
    # pagination_class = None
    
    def create(self, request, *args, **kwargs):
        data = request.data
        print(data)
        is_multi_variant = data.get('is_multi_variant', 'false').lower() == 'true'
        variants_data = self._extract_variants_data(data)
        images_data = self._extract_images_data(data)

        with transaction.atomic():
            try:
                product_serializer = self.get_serializer(data=data)
                product_serializer.is_valid(raise_exception=True)
                product = product_serializer.save()

                if is_multi_variant:
                    self._create_variants(variants_data, product)
                else:
                    self._create_single_variant(data, product)
                self._save_images(images_data, product)

                headers = self.get_success_headers(product_serializer.data)
                return Response(product_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except ValidationError as ve:
                transaction.set_rollback(True)
                return Response({'error': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                transaction.set_rollback(True)
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _extract_variants_data(self, data):
        variants_data = []
        index = 0
        while True:
            size = data.get(f'variants[{index}][size]')
            price = data.get(f'variants[{index}][price]')
            stock = data.get(f'variants[{index}][stock]')
            discount = data.get(f'variants[{index}][discount]')
            if size or price or stock or discount:
                variant = {
                    'size': size,
                    'price': price,
                    'stock': stock,
                    'discount': discount
                }
                variants_data.append(variant)
                index += 1
            else:
                break
        return variants_data

    def _extract_images_data(self, data):
        images_data = []
        index = 0
        while True:
            image = data.get(f'images[{index}]')
            if image:
                images_data.append(image)
                index += 1
            else:
                break
        return images_data

    def _create_variants(self, variants_data, product):
        for variant_data in variants_data:
            variant_data['product'] = product.id
            variant_serializer = ProductVariantSerializer(data=variant_data)
            variant_serializer.is_valid(raise_exception=True)
            variant_serializer.save()

    def _create_single_variant(self, single_variant_data, product):
        single_variant_data['product'] = product.id
        variant_serializer = ProductVariantSerializer(data=single_variant_data)
        variant_serializer.is_valid(raise_exception=True)
        variant_serializer.save()

    def _save_images(self, images_data, product):
        for image in images_data:
            if image:
                image_data = {'product': product.id, 'image': image}
                image_serializer = ProductImageSerializer(data=image_data)
                image_serializer.is_valid(raise_exception=True)
                image_serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        productslug = self.request.query_params.get('productslug')
        
        if productslug:
            queryset = queryset.filter(productslug=productslug)
        else:        
            category = self.request.query_params.get('category')
            categoryslug = self.request.query_params.get('categoryslug')
            subcategory = self.request.query_params.get('subcategory')
            subcategoryslug = self.request.query_params.get('subcategoryslug')
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            search = self.request.query_params.get('search')

            filters = Q()
            if category:
                filters &= Q(category__name__icontains=category)
            if categoryslug:
                filters &= Q(category__categoryslug__icontains=categoryslug)
            if subcategory:
                filters &= Q(subcategory__name__icontains=subcategory)
            if subcategoryslug:
                filters &= Q(subcategory__subcategoryslug__icontains=subcategoryslug)
            if min_price:
                filters &= Q(productvariant__price__gte=min_price)
            if max_price:
                filters &= Q(productvariant__price__lte=max_price)
            if search:
                filters &= Q(product_name__icontains=search) | Q(description__icontains=search)
            queryset = queryset.filter(filters).distinct()
        
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        recommended_products = get_recommended_products(request.user)
        serializer = self.get_serializer(recommended_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def trending(self, request):
        trending_products = self.get_trending_products()
        serializer = self.get_serializer(trending_products, many=True)
        return Response(serializer.data)

    def get_trending_products(self):
        past_week = timezone.now() - timezone.timedelta(days=7)
        trending_keywords = SearchHistory.objects.filter(
            search_date__gte=past_week
        ).values('keyword').annotate(
            count=Count('keyword')
        ).order_by('-count')[:5]

        if trending_keywords:
            keyword = trending_keywords[0]['keyword']
            trending_products = Product.objects.filter(
                Q(product_name__icontains=keyword)
            ).distinct()[:10]
        else:
            trending_products = Product.objects.none()

        return trending_products

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def get_products_by_ids(self, request):
        ids = request.query_params.get('ids', None)
        if ids:
            ids_list = ids.split(',')
            queryset = self.queryset.filter(id__in=ids_list)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request, 'is_detail': False})
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True, context={'request': request, 'is_detail': False})
            return Response(serializer.data)
        else:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        

    @method_decorator(cache_page(60*15))  # Cache for 15 minutes    def retrieve(self, request, *args, **kwargs):
    def retrieve(self, request, *args, **kwargs):
        productslug = request.query_params.get('productslug')
        if productslug:
            instance = get_object_or_404(self.get_queryset(), productslug=productslug)
        else:
            instance = self.get_object()
        
        serializer = self.get_serializer(instance, context={'request': request, 'is_detail': True})
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        productslug = request.query_params.get('productslug')
        if productslug:
            # Get the single product object based on the slug
            instance = get_object_or_404(self.get_queryset(), productslug=productslug)
            serializer = self.get_serializer(instance, context={'request': request, 'is_detail': True})
            return Response(serializer.data)
        else:
            # Use pagination for other cases
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request, 'is_detail': False})
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True, context={'request': request, 'is_detail': False})
            return Response(serializer.data)

def get_recommended_products(self, user):
    search_history = SearchHistory.objects.filter(user=user).values_list('keyword', flat=True)
    if not search_history:
        return Product.objects.order_by('?')[:5]  # Return 5 random products

    keyword_counter = Counter(search_history)
    most_searched_keywords = [keyword for keyword, _ in keyword_counter.most_common(3)]
    query = Q()
    for keyword in most_searched_keywords:
        query |= Q(product_name__icontains=keyword)

    recommended_products = Product.objects.filter(query).distinct()[:10]
    return recommended_products

class TrendingView(APIView):
    def get(self, request, format=None):
        past_week = timezone.now() - timezone.timedelta(days=7)
        trending_keywords = SearchHistory.objects.filter(
            search_date__gte=past_week
        ).values('keyword').annotate(
            count=Count('keyword')
        ).order_by('-count')[:5]

        if trending_keywords:
            keyword = trending_keywords[0]['keyword']
            trending_products = Product.objects.filter(
                Q(product_name__icontains=keyword)
            ).distinct()
        else:
            trending_products = Product.objects.none()

        serializer = ProductSerializer(trending_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RecommendationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        if request.user.is_authenticated:
            user = request.user
            recommended_products = self.get_recommended_products(user)
        else:
            product_id = request.query_params.get('product_id')
            if product_id:
                recommended_products = self.get_similar_products(product_id)
                if isinstance(recommended_products, Response):
                    return recommended_products
            else:
                return Response({"detail": "Product ID is required for unauthenticated users."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ProductSerializer(recommended_products, many=True, context={'request': request, 'is_detail': False})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_similar_products(self, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        similar_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:10]
        return similar_products

    def get_recommended_products(self, user):
        search_history = SearchHistory.objects.filter(user=user).values_list('keyword', flat=True)
        if not search_history:
            return Product.objects.order_by('?')[:5]  # Return 5 random products

        keyword_counter = Counter(search_history)
        most_searched_keywords = [keyword for keyword, _ in keyword_counter.most_common(3)]
        query = Q()
        for keyword in most_searched_keywords:
            query |= Q(product_name__icontains=keyword)

        recommended_products = Product.objects.filter(query).distinct()[:10]
        return recommended_products


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related('variant').all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('product', 'user').all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('product', 'user').all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommentReplyViewSet(viewsets.ModelViewSet):
    queryset = CommentReply.objects.select_related('comment', 'user').all()
    serializer_class = CommentReplySerializer
    permission_classes = [permissions.IsAuthenticated]

class NotifyUserViewSet(viewsets.ModelViewSet):
    queryset = NotifyUser.objects.select_related('product', 'user').all()
    serializer_class = NotifyUserSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product_id')
        variant = self.request.query_params.get('variant')

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if variant:
            queryset = queryset.filter(variant=variant)

        return queryset
    
    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        product = get_object_or_404(Product, id=request.data.get('product'))
        variant = request.data.get('variant')
        user = request.user if request.user.is_authenticated else None

        notify_user = NotifyUser.objects.create(
            product=product,
            variant=variant,
            user=user,
            email=email
        )

        self.create_notifications(user, product, email)

        serializer = self.get_serializer(notify_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def create_notifications(self, user, product, email):
        # Create notification for the user who posted
        if user:
            Notification.objects.create(
                user=user,
                title="Thank you For Your Intrest",
                message=f"We will nofify you as {product.product_name} get restock in the Store by {email}.",
                type="product_requested"
            )
            user_identifier = user.first_name
        else:
            user_identifier = email

        # Create notifications for all users with role 'admin' or 'staff'
        admin_staff_users = User.objects.filter(role__in=['admin', 'staff','Admin','Staff'])
        for admin_user in admin_staff_users:
            Notification.objects.create(
                user=admin_user,
                title=f"Product Requested {product.product_name}",
                message=f"{product.product_name} is been requested by user {user_identifier}",
                type="product_requested"
            )

    def list(self, request, *args, **kwargs):
        product_id = request.query_params.get('product')
        variant = request.query_params.get('variant')
        user = request.user if request.user.is_authenticated else None

        if product_id and variant:
            if user:
                queryset = get_object_or_404(self.queryset, product_id=product_id, variant=variant, user=user)
                return Response({"requested": True})
            else:
                return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
        
        queryset = self.queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)