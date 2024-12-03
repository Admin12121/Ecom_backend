from rest_framework import serializers
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, ReviewImage, Comment, CommentReply, NotifyUser, AddtoCart


class CategoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'categoryslug', 'image']


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

class ImageDataSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()    
    class Meta:
        model = ProductImage
        fields = ['image']

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    categoryname = serializers.SerializerMethodField()
    subcategoryname = serializers.SerializerMethodField()    
    comments = serializers.SerializerMethodField()    
    rating = serializers.SerializerMethodField()  # Add this line
    total_ratings = serializers.SerializerMethodField()  # Add this line

    class Meta:
        model = Product
        fields = '__all__'
    
    def get_categoryname(self, obj):
        return obj.category.name if obj.category else None

    def get_subcategoryname(self, obj):
        return obj.subcategory.name if obj.subcategory else None

    def get_comments(self, obj):
        request = self.context.get('request')
        if request and request.method == 'GET' and self.context.get('is_detail', False):
            comments = obj.comments.all()
            return CommentSerializer(comments, many=True, context=self.context).data
        return None

    def get_rating(self, obj):
        return obj.get_average_rating()

    def get_total_ratings(self, obj):  # Add this method
        return obj.get_total_ratings()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')
        if request and request.method == 'GET':
            variants = instance.productvariant_set.all()
            images = instance.images.all()
            if self.context.get('is_detail', False):
                comments = instance.comments.all()
                representation['comments'] = CommentSerializer(comments, many=True, context=self.context).data


            variants_data = ProductVariantSerializer(variants, many=True).data
            if len(variants_data) == 1:
                representation['variants'] = variants_data[0]
            else:
                representation['variants'] = variants_data 
            representation['images'] = ImageDataSerializer(images, many=True, context= self.context).data
            representation['categoryname'] = self.get_categoryname(instance)
            representation['subcategoryname'] = self.get_subcategoryname(instance)            

            # Remove reviews and comments if they are None or empty list
            if representation['comments'] is None:
                del representation['comments']
                
        return representation

class ProductByIdsSerializer(serializers.ModelSerializer):
    categoryname = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = '__all__'

    def get_categoryname(self, obj):
        return obj.category.name if obj.category else None        
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.method == 'GET':
            variants = instance.productvariant_set.all()
            images = instance.images.first()
            variants_data = ProductVariantSerializer(variants, many=True).data
            if len(variants_data) == 1:
                representation['variants'] = variants_data[0]
            else:
                representation['variants'] = variants_data 
            representation['images'] = ImageDataSerializer(images, context= self.context).data
            representation['categoryname'] = self.get_categoryname(instance)
        return representation



class ReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class ReviewImageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = '__all__'

class ReviewImageSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()
    class Meta:
        model = ReviewImage
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
class ReviewSerializer(serializers.ModelSerializer):
    review_images = ReviewImageSerializer(many=True, read_only=True)
    class Meta:
        model = Review
        fields = ['user', 'rating', 'title', 'content', 'recommended', 'delivery', 'review_images', 'created_at',]


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.method == 'GET':
            representation['review_images'] = ReviewImageSerializer(instance.review_images.all(), many=True, context=self.context).data
        return representation

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class CommentReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentReply
        fields = '__all__'

class NotifyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotifyUser
        fields = '__all__'    

class AddtoCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddtoCart
        fields = '__all__'

       
class ReviewWithProductSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    productslug = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    review_images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['user', 'rating', 'title', 'content', 'recommended', 'delivery', 'review_images', 'created_at', 'product_name', 'productslug', 'category_name', 'product_image']

    def get_product_name(self, obj):
        return obj.product.product_name if obj.product else None
    
    def get_productslug(self, obj):
        return obj.product.productslug if obj.product else None

    def get_category_name(self, obj):
        return obj.product.category.name if obj.product and obj.product.category else None

    def get_product_image(self, obj):
        request = self.context.get('request')
        image_instance = obj.product.images.first()
        if image_instance:
            return request.build_absolute_uri(image_instance.image.url)
        
        return None
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.method == 'GET':
            representation['review_images'] = ReviewImageSerializer(instance.review_images.all(), many=True, context=self.context).data
        return representation