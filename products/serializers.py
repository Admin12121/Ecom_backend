from rest_framework import serializers
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, Comment, CommentReply, NotifyUser, AddtoCart


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
    reviews = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_categoryname(self, obj):
        return obj.category.name if obj.category else None

    def get_subcategoryname(self, obj):
        return obj.subcategory.name if obj.subcategory else None

    def get_reviews(self, obj):
        request = self.context.get('request')
        if request and request.method == 'GET' and self.context.get('is_detail', False):
            reviews = obj.reviews.all()
            return ReviewSerializer(reviews, many=True, context=self.context).data
        return None

    def get_comments(self, obj):
        request = self.context.get('request')
        if request and request.method == 'GET' and self.context.get('is_detail', False):
            comments = obj.comments.all()
            return CommentSerializer(comments, many=True, context=self.context).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')
        if request and request.method == 'GET':
            variants = instance.productvariant_set.all()
            images = instance.images.all()
            if self.context.get('is_detail', False):
                reviews = instance.reviews.all()
                comments = instance.comments.all()

                representation['reviews'] = ReviewSerializer(reviews, many=True, context=self.context).data
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
            if representation['reviews'] is None:
                del representation['reviews']
            if representation['comments'] is None:
                del representation['comments']
                
        return representation
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

class NotifyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotifyUser
        fields = '__all__'    

class AddtoCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddtoCart
        fields = '__all__'