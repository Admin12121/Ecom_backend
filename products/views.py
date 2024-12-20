import re
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from accounts.models import User
from notification.models import Notification
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q, Prefetch, Max, Min, Sum
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


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.prefetch_related('subcategory_set').all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryViewSerializer
        return CategorySerializer    

    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated])
    def get_category(self, request, *args, **kwargs):
        category = Category.objects.all().order_by('-id')
        page = self.paginate_queryset(category)
        if page is not None:
            serializer = CategorySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = CategorySerializer(category, many=True, context={'request': request})
        return Response(serializer.data)

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
    
    def create(self, request, *args, **kwargs):
        data = request.data
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
            id = data.get(f'variants[{index}][id]')
            size = data.get(f'variants[{index}][size]')
            price = data.get(f'variants[{index}][price]')
            stock = data.get(f'variants[{index}][stock]')
            discount = data.get(f'variants[{index}][discount]')
            if size or price or stock or discount:
                variant = {
                    'id': id,
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
        for index, image in enumerate(images_data):
            if image:
                image_index = self.request.data.get(f'imageIndex[{index}]')
                image_data = {'product': product.id, 'image': image, 'index': image_index}
                image_serializer = ProductImageSerializer(data=image_data)
                image_serializer.is_valid(raise_exception=True)
                image_serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        user = self.request.user

        if not user.is_authenticated or not user.is_staff:
            queryset = queryset.filter(deactive=False)

        productslug = params.get('productslug')
        search = params.get('search')
        if productslug:
            queryset = queryset.filter(productslug=productslug)
            if not queryset.exists():
                raise Http404("Product not found")
            return queryset
        filters = Q()
        
        if search:
            filters &= Q(product_name__icontains=search) | Q(description__icontains=search)

        filters &= self._build_category_filters(params)
        filters &= self._build_price_filters(params)
        filters &= self._build_attribute_filters(params)

        queryset = queryset.annotate(
            min_variant_price=Min('productvariant__price'),
            max_variant_price=Max('productvariant__price'),
            sales_count=Sum('productvariant__saled_products__qty'),
            total_variant_stock=Sum('productvariant__stock'),
        )

        queryset = self._apply_ordering(queryset, params.get('filter'))

        queryset = queryset.filter(filters).distinct()
        return queryset

    def _build_category_filters(self, params):
        filters = Q()
        category = params.get('category')
        categoryslug = params.get('categoryslug')
        subcategory = params.get('subcategory')
        subcategoryslug = params.get('subcategoryslug')

        if category:
            filters &= Q(category__name__icontains=category)
        if categoryslug:
            filters &= Q(category__categoryslug__icontains=categoryslug)
        if subcategory:
            filters &= Q(subcategory__name__icontains=subcategory)
        if subcategoryslug:
            filters &= Q(subcategory__subcategoryslug__icontains=subcategoryslug)

        return filters

    def _build_price_filters(self, params):
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        price_filter = Q()

        if min_price:
            price_filter &= Q(productvariant__price__gte=min_price)
        if max_price:
            price_filter &= Q(productvariant__price__lte=max_price)

        return price_filter

    def _build_attribute_filters(self, params):
        """Build attribute-related filters like color, size, and metal."""
        filters = Q()
        attributes = {
            'color': 'description__icontains',
            'size': 'description__icontains',
            'metal': 'description__icontains'
        }

        for attr, query_field in attributes.items():
            param = params.get(attr, '')
            values = [v.strip() for v in param.split(',') if v.strip()]
            values += [v.strip() for v in params.getlist(attr) if v.strip()]
            if values:
                attr_filter = Q()
                for value in values:
                    attr_filter |= Q(**{query_field: f'#{value}'})
                filters &= attr_filter

        # Handle stock filter
        stock_filter = params.get('stock')
        if stock_filter == 'in':
            filters &= Q(total_variant_stock__gt=0)
        elif stock_filter == 'out':
            filters &= Q(total_variant_stock__lte=0)

        return filters

    def _apply_ordering(self, queryset, order_by):
        """Apply ordering based on filter parameter."""
        ordering_map = {
            'bestselling': '-sales_count',
            'newin': '-id',
            'hightolow': '-min_variant_price',
            'lowtohigh': 'min_variant_price'
        }
        return queryset.order_by(ordering_map.get(order_by, '-id'))

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        is_multi_variant = data.get('is_multi_variant', 'false').lower() == 'true'
        instance.product_name = data.get('product_name', instance.product_name)
        instance.description = data.get('description', instance.description)
        instance.category_id = data.get('category', instance.category_id)
        instance.subcategory_id = data.get('subcategory', instance.subcategory_id)
        
        instance.save()

        if is_multi_variant:
            variants_data = self._extract_variants_data(data)
            self._update_variants(variants_data, instance)
        else:
            single_variant_data = {
                'size': data.get('size'),
                'price': data.get('price'),
                'stock': data.get('stock'),
                'discount': data.get('discount')
            }
            existing_variant = instance.productvariant_set.first()
            if existing_variant:
                existing_variant.price = single_variant_data['price']
                existing_variant.stock = single_variant_data['stock']
                existing_variant.discount = single_variant_data['discount']
                existing_variant.save()

        return Response({'msg': 'Product updated successfully'}, status=status.HTTP_200_OK)

    def _update_variants(self, variants_data, product):
        existing_variants = {variant.id: variant for variant in product.productvariant_set.all()}

        for variant_data in variants_data:
            variant_id = variant_data.get('id')
            if variant_id:
                variant_id = int(variant_id)
            else:
                variant_id = None
            size = variant_data.get('size')

            if variant_id and variant_id in existing_variants:
                variant = existing_variants[variant_id]
                variant.size = size
                variant.price = variant_data['price']
                variant.stock = variant_data['stock']
                variant.discount = variant_data['discount']
                variant.save()
            else:
                if any(v.size == size for v in existing_variants.values()):
                    raise ValidationError(f"Variant with size '{size}' already exists for this product.")
                print(product.id)
                variant_data['product'] = product.id
                variant_data.pop('id', None)
                variant_serializer = ProductVariantSerializer(data=variant_data)
                variant_serializer.is_valid(raise_exception=True)
                variant_serializer.save()

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
        all_flag = request.query_params.get('all', 'false').lower() == 'true'  # Check for 'all' flag
        if ids:
            ids_list = ids.split(',')
            queryset = self.queryset.filter(id__in=ids_list)
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request, 'is_detail': False}) if all_flag else ProductByIdsSerializer(page, many=True, context={'request': request, 'is_detail': False})
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True, context={'request': request, 'is_detail': False}) if all_flag else ProductByIdsSerializer(queryset, many=True, context={'request': request, 'is_detail': False})
            return Response(serializer.data)
        else:
            return Response({"error": "No IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
    @method_decorator(cache_page(60*15))
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deactive = not instance.deactive
        instance.save()
        return Response({"message":"Product deleted successfull"},status=status.HTTP_200_OK)

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

        if not trending_keywords:
            # Fallback to all-time search if past week's search yields no results
            trending_keywords = SearchHistory.objects.values('keyword').annotate(
                count=Count('keyword')
            ).order_by('-count')[:5]

        if trending_keywords:
            keyword = trending_keywords[0]['keyword']
            trending_products = Product.objects.filter(
                Q(product_name__icontains=keyword)
            ).distinct()
        else:
            trending_products = Product.objects.none()

        # If no trending products found, fallback to latest created products
        if not trending_products.exists():
            trending_products = Product.objects.order_by('-id')[:4]

        serializer = ProductSerializer(trending_products, many=True, context={'request': request, 'is_detail': False})
        return Response(serializer.data, status=status.HTTP_200_OK)

class RecommendationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        if request.user.is_authenticated:
            product_id = request.query_params.get('product_id')
            user = request.user
            recommended_products = self.get_recommended_products(user, product_id)
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

    def get_recommended_products(self, user, product_id=None):
        search_history = SearchHistory.objects.filter(user=user).values_list('keyword', flat=True)
            
        if not search_history:
            return Product.objects.order_by('?')[:5]  # Return 5 random products

        keyword_counter = Counter(search_history)
        most_searched_keywords = [keyword for keyword, _ in keyword_counter.most_common(3)]
        query = Q()
        for keyword in most_searched_keywords:
            query |= Q(product_name__icontains=keyword)

        recommended_products = Product.objects.filter(query).distinct()
        if product_id:
            recommended_products = recommended_products.exclude(id=product_id)
        return recommended_products[:10]

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({ "message" : "Variant Deleted"}, status=status.HTTP_200_OK)    

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({ "message" : "Image Updated"}, status=status.HTTP_200_OK) 

    def destroy(self, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({ "message" : "Image Removed"}, status=status.HTTP_200_OK)    

class ReviewPostViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('product', 'user').all().order_by('-id')
    serializer_class = ReviewWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id
        data['product']  = Product.objects.get(productslug=data.get('product_slug')).id
        image = data.pop('image', None)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                self.perform_create(serializer)
                image = request.FILES.get('image')
                if image:
                    try:
                        data = {'review': serializer.data['id'], 'image': image}
                        image_serializer = ReviewImageWriteSerializer(data=data)
                        image_serializer.is_valid(raise_exception=True)
                        image_serializer.save()
                    except Exception as e:
                        transaction.set_rollback(True)
                        raise e
        return Response({"msg": "Review Posted Successfully"}, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        if request.user.id != instance.user.id and request.user.role != 'Admin' and request.user.role != 'Staff':
            return Response({"detail": "You are not authorized to update this review data."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                self.perform_update(serializer)
                image = request.FILES.get('image')
                if image:
                    try:
                        review_image = ReviewImageWriteSerializer(review=instance, image=image)
                        review_image.save()
                    except Exception as e:
                        transaction.set_rollback(True)
                        raise e
        return Response({"msg": "Review Updated Successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])                
    def update_reviews(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        if request.user.id != instance.user.id and request.user.role != 'Admin' and request.user.role != 'Staff':
            return Response({"detail": "You are not authorized to update this review data."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"msg": "Review Updated Successfully"}, status=status.HTTP_200_OK)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('product', 'user').all().order_by('-id')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()
        product_slug = self.kwargs.get('product_slug')
        star = self.request.query_params.get('star')
        filter = self.request.query_params.get('filter')
        search = self.request.query_params.get('search')
        if product_slug:
            queryset = queryset.filter(product__productslug=product_slug)
        if self.request.user.is_authenticated:
            request_user = self.request.user
            if request_user.role != 'Admin' and request_user.role != 'Staff' and not request_user.is_superuser and not product_slug:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied({"detail": "You are not authorized to view reviews"})
        if star and star != '0':
            queryset = queryset.filter(rating=star)
        if search:
            queryset = queryset.filter(Q(product__product_name__icontains=search) | Q(user__username__icontains=search) | Q(user__first_name__icontains=search))
        if filter == 'recent':
            queryset = queryset.order_by('-created_at')
        elif filter == 'rating':
            queryset = queryset.order_by('-rating')
        elif filter == 'relevant':
            # Implement your logic for relevance sorting if needed
            pass        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def get_user_reviews(self, request, *args, **kwargs):
        user = request.user
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        reviews = self.get_queryset()
        if user.is_staff:
            reviews = reviews
        else:
            reviews = reviews.filter(user=user)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewWithProductSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = ReviewWithProductSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    
class AddToCartViewSet(viewsets.ModelViewSet):
    queryset = AddtoCart.objects.all()
    serializer_class = AddtoCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User, email = self.request.user)
        return self.queryset.filter(user=user)


    def create(self, request, *args, **kwargs):
        items = request.data.get('items', [])
        user = request.user
        cart_items = []
        
        for item in items:
            product = get_object_or_404(Product, id=item['id'])
            variant = get_object_or_404(ProductVariant, id=item['variantId'])
            pcs = item['pcs']
            existing_cart_item = AddtoCart.objects.filter(user=user, product=product, variant=variant)
            if existing_cart_item.exists():
                existing_cart_item.delete()
            cart_item = AddtoCart(user=user, product=product, variant=variant, pcs=pcs)
            cart_items.append(cart_item)

        AddtoCart.objects.bulk_create(cart_items)

        return Response({'msg': 'Added to Cart'}, status=status.HTTP_201_CREATED)
    
    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        data = request.data
        instance = AddtoCart.objects.get(user=request.user, product_id=data['product'], variant_id=data['variant'])
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['pcs'] > instance.variant.stock:
            return Response({'error': 'Not enough stock available'}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response({'msg': 'Cart Updated'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def cartdestroy(self, request, *args, **kwargs):
        user = request.user
        product_id = kwargs.get('product_id')
        variant_id = kwargs.get('variant_id')

        if not product_id or not variant_id:
            return Response({'error': 'Product ID or Variant ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = AddtoCart.objects.get(user=user, product_id=product_id, variant_id=variant_id)
            cart_item.delete()
            return Response({'msg': 'Item removed from cart'}, status=status.HTTP_200_OK)
        except AddtoCart.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)
        
class StocksView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        low_stock_products = Product.objects.filter(productvariant__stock__lt=5).distinct()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(low_stock_products, request)
        serializer = LowStockProductSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)