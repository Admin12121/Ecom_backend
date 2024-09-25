from rest_framework import viewsets, status, filters, serializers  # Added serializers import
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import SalesDataSerializer, RedeemSerializer
from .models import Sales, Redeem_Code, Saled_Products
from products.models import Product
from django.shortcuts import get_object_or_404
from django.db.models import F
from django.utils import timezone
from accounts.renderers import UserRenderer

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class SalesViewSet(viewsets.ModelViewSet):
    queryset = Sales.objects.all()
    serializer_class = SalesDataSerializer
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['costumer_name', 'date']
    search_fields = ['costumer_name__username', 'invoiceno']
    ordering_fields = ['date', 'total']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Sales.objects.all()
        return Sales.objects.filter(costumer_name=user)

    def perform_create(self, serializer):
        invoice_data = self.request.data.get('invoice_data', [])
        user = self.request.user
        sale = serializer.save(costumer_name=user)
        for data in invoice_data:
            product = get_object_or_404(Product, id=data['product_id'])
            quantity_sold = data['pcs']
            Product.objects.filter(id=product.id).update(quantity=F('quantity') - quantity_sold)
            Saled_Products.objects.create(
                transition=sale,
                product=product,
                product_name=data['product_name'],
                price=data['product_price'],
                qty=data['pcs'],
                total=data['total']
            )

class RedeemCodeViewSet(viewsets.ModelViewSet):
    queryset = Redeem_Code.objects.all()
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

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.valid < timezone.now().date():
            raise serializers.ValidationError({"message": "Redemption code is expired or inactive."})
        if instance.used >= instance.limit:
            raise serializers.ValidationError({"message": "Maximum limit reached for this redemption code."})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({'msg': f'Redeem code {name} deleted successfully'}, status=status.HTTP_200_OK)