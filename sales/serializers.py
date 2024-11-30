from rest_framework import serializers
from .models import *
from accounts.serializers import DeliveryAddressSerializer

class RedeemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redeem_Code
        fields = "__all__"


class Saled_ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saled_Products
        fields = "__all__"


class SalesDataSerializer(serializers.ModelSerializer):
    products = Saled_ProductsSerializer(many=True, read_only=True)
    costumer_name = serializers.SlugRelatedField(read_only=True, slug_field='username')
    shipping = DeliveryAddressSerializer()
    class Meta:
        model = Sales
        fields = "__all__"



