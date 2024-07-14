# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.views import APIView
# from .serializers import *
# from accounts.models import SearchHistory
# from accounts.renderers import UserRenderer
# from rest_framework.permissions import IsAuthenticated , IsAuthenticatedOrReadOnly
# from rest_framework.pagination import PageNumberPagination
# from ecom_backend import settings
# from django.db.models import F, Q
# from django.utils import timezone
# import json
# from datetime import datetime
# import random
# from django.shortcuts import get_object_or_404
# from collections import Counter

# import random

# from django.utils import timezone


# class TrendingView(APIView):
#     def get(self, request, format=None):
#         all_time_trending_keywords = self.get_trending_keywords(all_time=True)
#         this_week_top_search_keywords = self.get_trending_keywords(all_time=False)
#         all_time_best_performing_products = self.get_best_performing_products()
#         trending_data = {
#             'all_time_trending_keywords': all_time_trending_keywords,
#             'this_week_top_search_keywords': this_week_top_search_keywords,
#             'all_time_best_performing_products': all_time_best_performing_products,
#         }

#         return Response(trending_data, status=status.HTTP_200_OK)

#     def get_trending_keywords(self, all_time=True):
#         if all_time:
#             search_history = SearchHistory.objects.all()
#         else:
#             start_date = timezone.now() - timezone.timedelta(days=7)
#             search_history = SearchHistory.objects.filter(search_date__gte=start_date)

#         keyword_counter = Counter([history.keyword for history in search_history])
#         trending_keywords = [keyword for keyword, _ in keyword_counter.most_common(3)]
#         trending_products = Products.objects.filter(product_name__icontains=trending_keywords[0]).distinct()

#         return trending_products

#     def get_best_performing_products(self):
#         product_counter = Counter([history.product for history in SearchHistory.objects.all()])
#         best_performing_products = [product for product, _ in product_counter.most_common(3)]
#         trending_products = Products.objects.filter(product_name__in=best_performing_products).distinct()

#         return trending_products


# def get_recommended_products(user):
#     search_history = SearchHistory.objects.filter(user=user)
#     if not search_history.exists():
#         return Products.objects.order_by('?')[:10]  # Return 10 random products

#     keywords = [history.keyword for history in search_history]
#     keyword_counter = Counter(keywords)
#     most_searched_keywords = keyword_counter.most_common(3)
#     recommended_keywords = [keyword[0] for keyword in most_searched_keywords]
#     recommended_products = Products.objects.filter(
#         product_name__icontains=recommended_keywords[0]
#     ).distinct()
#     return recommended_products

# class RecommendationView(APIView):
#     def get(self, request, format=None):
#         user = request.user
#         recommended_products = get_recommended_products(user)
#         serializer = ProductsSerializer(recommended_products, many=True, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)


# class CategoryView(APIView):
#     renderer_classes = [UserRenderer]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, format=None):
#           category = request.query_params.get('name')

#           if category:
#               category = Category.objects.filter(category__icontains=category)
#           else:
#               category = Category.objects.all()
#           serializer = CategorySerializer(category, many=True,context={'request': request})
#           return Response(serializer.data, status=status.HTTP_200_OK)

#     def post(self, request, format=None):
#         serializer = CategorySerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         category = request.data.get('category')
#         if(Category.objects.filter(category=category)).exists():
#             return Response({'error': f'{category} already exists in this store'}, status=status.HTTP_400_BAD_REQUEST)

#         serializer.save()
#         return Response({'msg': 'Category added'}, status=status.HTTP_201_CREATED)
   
#     def patch(self,request,*args,**kwargs):
#       id = request.query_params.get('id')
#       if id:
#         try:
#           category = Category.objects.get(id=id)
#           category_name = category.category
#           serializer = CategorySerializer(category,data=request.data, partial= True)
#           if serializer.is_valid():
#              serializer.save()
#              return Response({'msg': f'Category {category_name} updated'}, status=status.HTTP_200_OK)
#           return Response({'msg': 'invalid data'}, status=status.HTTP_403_FORBIDDEN)
#         except Exception as e:
#             return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)
    
#     def delete(self, request, *args, **kwargs):
#         id = request.query_params.get('id')
#         if id:
#             try:
#                 category = Category.objects.get(id=id)
#                 category_name = category.category
#                 category.delete()
#                 return Response({'msg': f'Category {category_name} deleted successfully'}, status=status.HTTP_200_OK)
#             except Exception as e:
#                 return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)

# class ProductsView(APIView):
#     renderer_classes = [UserRenderer]
#     # permission_classes = [IsAuthenticated]

#     # def post(self, request, format=None):
#     #     serializer = ProductsSerializer(data=request.data)

#     #     cat = request.data.get('category')
#     #     variable_data = request.data.get('rowData')
#     #     user = self.request.user
#     #     images_data = request.FILES.getlist('preview_images')

#     #     category = get_object_or_404(Category, id=cat)
#     #     products = request.data.get('product_name')

#     #     if Products.objects.filter(product_name=products).exists():
#     #         return Response({'errors': {'product_name': [f'{products} already exists in this store.']}}, status=status.HTTP_400_BAD_REQUEST)
#     #     else:
#     #         if serializer.is_valid(raise_exception=True):
#     #             product = serializer.save(category=category, createdby=user)
#     #             for img_data in images_data:
#     #                 Product_images.objects.create(product=product, preview_image=img_data)

#     #             try:
#     #                 variant_data = json.loads(variable_data)  # Parse the JSON data
#     #                 for data in variant_data:
#     #                     variant_category_name = data.get('variantion')  # Corrected key name
#     #                     variant_values = data.get('variantValues')  # Corrected key name
#     #                     quantity_alert = data.get('quantity_alert')
#     #                     quantity = data.get('quantity')
#     #                     price = data.get('price')

#     #                     variant_category, _ = Varient_Category.objects.get_or_create(product=product, name=variant_category_name)

#     #                     variant_ids = []  # Store variant IDs for each variant combination
#     #                     for varient_name, value in variant_values.items():
#     #                         varient_category, _ = Varient_Category.objects.get_or_create(product=product, name=varient_name)
#     #                         variant_name_obj, _ = Varient_name.objects.get_or_create(product=product, varient_category=varient_category, name=value)
#     #                         variant_ids.append(variant_name_obj.id)  # Add variant ID to the list

#     #                     # Create a single Varientdata instance for each combination
#     #                     variant_data_obj = Varientdata.objects.create(product=product, name=None, quantity_alert=quantity_alert, quantity=quantity, price=price)
#     #                     variant_data_obj.varient.add(*variant_ids)  # Add all variant IDs to the many-to-many relationship

#     #             except Exception as e:
#     #                 print("Error:", e)

#     #             return Response({'msg': 'Product Saved'}, status=status.HTTP_200_OK)
#     #         else:
#     #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def get(self, request, format=None):
#           product_name = request.query_params.get('product_name')
#           id = request.query_params.get('id')

#           if product_name:
#               product = Products.objects.filter( product_name__icontains=product_name)
#           elif product_name and id:
#                 product = Products.objects.filter(product_name=product_name, id=id)
#           else:
#               product = Products.objects.all()
#           serializer = ProductsSerializer(product, many=True,context={'request': request})
#           return Response(serializer.data, status=status.HTTP_200_OK)


#     # def delete(self, request, *args, **kwargs):
#     #     id = request.query_params.get('id')
#     #     if id:
#     #         try:
#     #             product = Products.objects.get(id=id)
#     #             product_name = product.product_name
#     #             product.delete()
#     #             return Response({'msg': f'{product_name} is deleted successfully'}, status=status.HTTP_200_OK)
#     #         except Exception as e:
#     #             return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)

# class ProductImageView(APIView):
#     def post(self, request, format=None):
#         serializer = ProductImageSerializer(data=request.data)
#         product = request.data.get('product')
#         try:
#             product = Products.objects.get(id = product)
#         except Products.DoesNotExist:
#             return Response({'error':'Product does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        
#         if serializer.is_valid(raise_exception=True):
#         #    serializer.save(product = product)
#            return Response({'msg':'Product images Saved'}, status=status.HTTP_200_OK)
#         else: 
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class ForeignKeyView(APIView):
#     renderer_classes = [UserRenderer]
#     permission_classes = [IsAuthenticated]

#     def get(self, request, format=None):

#           categories = Category.objects.all()
#           varient_category = [
#               {"varient":"Color"},
#               {"varient":"Size"},
#               {"varient":"Memory"},
#           ]
#           serializer = {
#             'categories': CategoryListSerializer(categories, many=True).data,
#             'varient_category' : varient_category
#            }
#           return Response(serializer, status=status.HTTP_200_OK)


from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, Comment, CommentReply
from .serializers import (CategorySerializer, SubcategorySerializer, ProductSerializer,
                          ProductVariantSerializer, ProductImageSerializer, ReviewSerializer, CommentSerializer,
                          CommentReplySerializer)

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

    # def get_serializer_class(self):
    #     if self.request.method == 'GET':
    #         return CategorySerializer
    #     return CategorySerializer

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
            subcategory = self.request.query_params.get('subcategory')
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            search = self.request.query_params.get('search')

            filters = Q()
            if category:
                filters &= Q(category__name__icontains=category)
            if subcategory:
                filters &= Q(subcategory__name__icontains=subcategory)
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        recommended_products = get_recommended_products(user)
        serializer = ProductSerializer(recommended_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

def get_recommended_products(user):
    search_history = SearchHistory.objects.filter(user=user)
    if not search_history.exists():
        return Product.objects.order_by('?')[:10]  # Return 10 random products

    keywords = search_history.values_list('keyword', flat=True)
    keyword_counter = Counter(keywords)
    most_searched_keywords = [keyword for keyword, _ in keyword_counter.most_common(3)]
    recommended_products = Product.objects.filter(
        Q(product_name__icontains=most_searched_keywords[0]) |
        Q(product_name__icontains=most_searched_keywords[1]) |
        Q(product_name__icontains=most_searched_keywords[2])
    ).distinct()

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

