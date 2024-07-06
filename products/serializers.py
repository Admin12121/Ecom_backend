from rest_framework import serializers
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, Comment, CommentReply


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True, source='subcategory_set') 

    class Meta:
        model = Category
        fields = ['id', 'name', 'categoryslug', 'subcategories']
        
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ProductVariantSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(source='variants.images', many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        is_multi_variant = validated_data.pop('is_multi_variant', False)
        variants_data = validated_data.pop('variants', [])
        product = Product.objects.create(**validated_data, is_multi_variant=is_multi_variant)

        if is_multi_variant:
            for variant_data in variants_data:
                images_data = variant_data.pop('images', [])
                variant = ProductVariant.objects.create(product=product, **variant_data)
                for image_data in images_data:
                    ProductImage.objects.create(variant=variant, **image_data)
        else:
            # Create a single variant if is_multi_variant is False
            images_data = variants_data.pop('images', [])
            variant = ProductVariant.objects.create(product=product, **variants_data[0])
            for image_data in images_data:
                ProductImage.objects.create(variant=variant, **image_data)

        return product

    def update(self, instance, validated_data):
        is_multi_variant = validated_data.pop('is_multi_variant', instance.is_multi_variant)
        variants_data = validated_data.pop('variants', [])
        
        instance.product_name = validated_data.get('product_name', instance.product_name)
        instance.description = validated_data.get('description', instance.description)
        instance.category = validated_data.get('category', instance.category)
        instance.subcategory = validated_data.get('subcategory', instance.subcategory)
        instance.is_multi_variant = is_multi_variant
        instance.save()

        if is_multi_variant:
            for variant_data in variants_data:
                variant_id = variant_data.get('id')
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, product=instance)
                    variant.size = variant_data.get('size', variant.size)
                    variant.price = variant_data.get('price', variant.price)
                    variant.stock = variant_data.get('stock', variant.stock)
                    variant.discount = variant_data.get('discount', variant.discount)
                    variant.save()
                else:
                    images_data = variant_data.pop('images', [])
                    variant = ProductVariant.objects.create(product=instance, **variant_data)
                    for image_data in images_data:
                        ProductImage.objects.create(variant=variant, **image_data)
        else:
            variant = ProductVariant.objects.get(product=instance)
            variant.size = variants_data[0].get('size', variant.size)
            variant.price = variants_data[0].get('price', variant.price)
            variant.stock = variants_data[0].get('stock', variant.stock)
            variant.discount = variants_data[0].get('discount', variant.discount)
            variant.save()

        return instance


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReply
        fields = '__all__'
