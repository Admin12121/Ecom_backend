from rest_framework import serializers
from .models import *

class RedeemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redeem_Code
        fields = "__all__"


class AddtoCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Add_to_Cart
        fields = "__all__"


class Saled_ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saled_Products
        fields = "__all__"


class SalesDataSerializer(serializers.ModelSerializer):
    products = Saled_ProductsSerializer(many=True, read_only=True)
    costumer_name = serializers.SlugRelatedField(read_only=True, slug_field='name')
    class Meta:
        model = Sales
        fields = "__all__"



