from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import *
from django.contrib.auth import authenticate
from accounts.renderers import UserRenderer
from rest_framework.permissions import IsAuthenticated , IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from ecom_backend import settings
from django.db.models import F
import random
from django.shortcuts import get_object_or_404
from products.models import Product
from django.utils import timezone

class SalesDataView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        user = request.user 

        if user.is_superuser:
            sales = Sales.objects.all()
        else:
            sales = Sales.objects.filter(costumer_name=user)

        serializer = SalesDataSerializer(sales, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, format=None):
            serializer = SalesDataSerializer(data=request.data)

            invoice_data = request.data.get('invoice_data', [])
            user = self.request.user

            if serializer.is_valid(raise_exception=True):
                sale = serializer.save( costumer_name=user)
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
                return Response({'msg':'Invoice Saved'}, status=status.HTTP_200_OK)
            else: 
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,*args,**kwargs):
      id = request.query_params.get('id')
      if id:
        try:
          sales = Sales.objects.get(id=id)
          invoiceno = sales.invoiceno
          serializer = SalesDataSerializer(sales,data=request.data, partial= True)
          if serializer.is_valid():
             serializer.save()
             return Response({'msg': f'Customer {invoiceno} updated'}, status=status.HTTP_200_OK)
          return Response({'msg': 'invalid data'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)
   
class Redeem_CodeView(APIView):
      renderer_classes = [UserRenderer]
      permission_classes = [IsAuthenticated]

      def get(self, request, format=None):
            code = request.query_params.get('code')
            if code:
                 redeem_codee = Redeem_Code.objects.filter(code=code)

            if redeem_codee.exists():
                  if len(redeem_codee) == 1:
                        redeem_code = redeem_codee.first()
                        if redeem_code.valid < timezone.now().date():
                              return Response({"message": "Redemption code is expired or inactive."}, status=status.HTTP_400_BAD_REQUEST)
                        elif redeem_code.used >= redeem_code.limit:
                               return Response({"message": "Maximum limit reached for this redemption code."}, status=status.HTTP_400_BAD_REQUEST)
                        else:
                              serializer = RedeemSerializer(redeem_codee, many=True)
                              return Response(serializer.data, status=status.HTTP_200_OK)
                  else:
                        serializer = RedeemSerializer(redeem_codee, many=True)
                        return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                  return Response({"message": "Redemption code does not exist for the provided store and code."}, status=status.HTTP_404_NOT_FOUND)                  
     
      def post(self, request, format=None):
            serializer = RedeemSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            name = request.data.get('name')
            code = request.data.get('code')

            if(Redeem_Code.objects.filter(code=code, name=name)).exists():
                  return Response({'error': f'{name} already exists in this store'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response({'msg': 'Redeem Code Created'}, status=status.HTTP_201_CREATED)
      
      def patch(self,request,*args,**kwargs):
            id = request.query_params.get('id')
            if id:
                  try:
                        redeemcode = Redeem_Code.objects.get(id=id)
                        name = redeemcode.name
                        serializer = RedeemSerializer(redeemcode,data=request.data, partial= True)
                        if serializer.is_valid():
                              serializer.save()
                              return Response({'msg': f'Reddem code {name} updated'}, status=status.HTTP_200_OK)
                        return Response({'msg': 'invalid data'}, status=status.HTTP_403_FORBIDDEN)
                  except Exception as e:
                        return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)
      
      def delete(self, request, *args, **kwargs):
            id = request.query_params.get('id')
            if id:
                  try:
                        redeem = Redeem_Code.objects.get(id=id)
                        name = redeem.name
                        redeem.delete()
                        return Response({'msg': f'Reddem code {name} deleted successfully'}, status=status.HTTP_200_OK)
                  except Exception as e:
                        return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)

class AddToCartView(APIView):
      renderer_classes = [UserRenderer]
      permission_classes = [IsAuthenticated]
 
      def get(self, request, format=None):
            user = self.request.user
            if user:
                cartdata = Add_to_Cart.objects.filter(user=user)
            else:
                cartdata = None

            serializer = AddtoCartSerializer(cartdata, many=True,context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

      def post(self, request, format=None):
            serializer = AddtoCartSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'msg': 'Added to Cart'}, status=status.HTTP_201_CREATED)
      
      def patch(self,request,*args,**kwargs):
            id = request.query_params.get('id')
            if id:
                  try:
                        redeemcode = Add_to_Cart.objects.get(id=id)
                        serializer = AddtoCartSerializer(redeemcode, data=request.data, partial= True)
                        if serializer.is_valid():
                              serializer.save()
                              return Response({'msg': f'Cart Updated'}, status=status.HTTP_200_OK)
                        return Response({'msg': 'invalid data'}, status=status.HTTP_403_FORBIDDEN)
                  except Exception as e:
                        return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)
      
      def delete(self, request, *args, **kwargs):
            id = request.query_params.get('id')
            if id:
                  try:
                        cart = Add_to_Cart.objects.get(id=id)
                        cart.delete()
                        return Response({'msg': f'Item removed from cart'}, status=status.HTTP_200_OK)
                  except Exception as e:
                        return Response({'msg': 'invalid id'}, status=status.HTTP_403_FORBIDDEN)
