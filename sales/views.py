from rest_framework import viewsets, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import SalesDataSerializer, RedeemSerializer, SalesPostDataSerializer
from .models import Sales, Redeem_Code, Saled_Products
from products.models import Product, ProductVariant
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils import timezone
from accounts.renderers import UserRenderer
from rest_framework.decorators import action
from django.db import transaction 
from accounts.models import DeliveryAddress
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Q, Prefetch
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SalesViewSet(viewsets.ModelViewSet):
    queryset = Sales.objects.all().order_by('-id')
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['costumer_name']
    search_fields = ['costumer_name__first_name', 'transactionuid', 'costumer_name__email']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SalesPostDataSerializer
        return SalesDataSerializer
    
    def retrieve(self, request, *args, **kwargs):
        transactionuid = kwargs.get('transactionuid')
        instance = get_object_or_404(Sales, transactionuid=transactionuid)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        search = self.request.query_params.get('search')
        filters = Q()
        if search:
            filters &= Q(costumer_name__first_name__icontains=search) | Q(transactionuid__icontains=search) | Q(costumer_name__email__icontains=search)
        queryset = self.queryset.filter(filters)
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(costumer_name=user)

    def perform_create(self, serializer):
        invoice_data = self.request.data.get('products', [])
        user = self.request.user
        redeem_data = self.request.data.get('redeemData')
        shipping = self.request.data.get('shipping')
        discount = self.request.data.get('discount')
        sub_total = self.request.data.get('sub_total')
        total_amt = self.request.data.get('total_amt')
        transactionuid = self.request.data.get('transactionuid')
        payment_intent_id = self.request.data.get('paymentIntentId')
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            shipping_instance = DeliveryAddress.objects.get(id=shipping)
        except DeliveryAddress.DoesNotExist:
            return Response({"error": "Invalid shipping address."}, status=status.HTTP_400_BAD_REQUEST)


        redeem_code_obj = None
        redeem_code_error = None
        with transaction.atomic():
            if redeem_data:
                try:
                    redeem_code_obj = Redeem_Code.objects.get(id=redeem_data["id"])
                    if redeem_code_obj.valid_until < timezone.now().date():
                        redeem_code_error = "Redeem code is expired."
                    elif redeem_code_obj.used >= redeem_code_obj.limit:
                        redeem_code_error = "Redeem code usage limit reached."
                    else:
                        redeem_code_obj.used += 1
                        redeem_code_obj.save()
                except Redeem_Code.DoesNotExist:
                    redeem_code_error = "Invalid redeem code - object does not exist."
            
            if redeem_code_error:
                return Response({"warning": redeem_code_error}, status=status.HTTP_201_CREATED)
        
            sale = serializer.save(
                costumer_name=user,
                redeem_data=redeem_code_obj.name if redeem_code_obj and redeem_code_obj.name else None,
                shipping=shipping_instance,
                discount=discount,
                sub_total=sub_total,
                total_amt=total_amt,
                transactionuid=transactionuid,
                payment_method=payment_intent_id
            )
            
            for data in invoice_data:
                product = get_object_or_404(Product, id=data['product'])
                variant = get_object_or_404(ProductVariant, id=data['variant'])
                quantity_sold = data['pcs']
                price = variant.price
                
                if variant.stock < quantity_sold:
                    raise serializers.ValidationError({"error": f"Not enough stock for product variant {variant.id}"})
                
                ProductVariant.objects.filter(id=variant.id).update(stock=F('stock') - quantity_sold)
                
                Saled_Products.objects.create(
                    transition=sale,
                    product=product,
                    variant=variant,
                    price=price,
                    qty=quantity_sold,
                    total=quantity_sold * price
                )

        return Response({"message": "payment complete"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='status/(?P<status_param>[^/.]+)')
    def filter_by_status(self, request, status_param=None):
        status_map = {
            'onshipping': ['pending', 'verified'],
            'arrived': ['proceed', 'packed'],
            'delivered': ['delivered', 'successful']
        }

        if status_param not in status_map:
            raise ValidationError({'error': 'Invalid status parameter'})

        queryset = self.filter_queryset(self.get_queryset().filter(status__in=status_map[status_param]))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RedeemCodeViewSet(viewsets.ModelViewSet):
    queryset = Redeem_Code.objects.all().order_by('-id')
    serializer_class = RedeemSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['code', 'name']
    search_fields = ['code', 'name']
    ordering_fields = ['valid', 'used']

    def get_queryset(self):
        code = self.request.query_params.get('code')
        if code:
            return Redeem_Code.objects.filter(code=code)
        return super().get_queryset()

    def perform_create(self, serializer):
        name = self.request.data.get('name')
        code = self.request.data.get('code')
        if Redeem_Code.objects.filter(code=code, name=name).exists():
            raise serializers.ValidationError({'error': f'{name} already exists in this store'})
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'msg': f'Redeem code {name} deleted successfully'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='verify-code')
    def verify_code(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            redeem_code = Redeem_Code.objects.get(code=code)
        except Redeem_Code.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=status.HTTP_404_NOT_FOUND)
        
        if redeem_code.valid_until < timezone.now().date():
            return Response({'error': 'Code is expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        if redeem_code.limit is not None and redeem_code.used >= redeem_code.limit:
            return Response({'error': 'Code usage limit reached'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = {
            'id': redeem_code.id,
            'type': redeem_code.type,
            'discount': redeem_code.discount,
            'minimum': redeem_code.minimum,
            'limit': redeem_code.limit,
        }
        return Response(data, status=status.HTTP_200_OK)    