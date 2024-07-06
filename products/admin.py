from django.contrib import admin
from .models import Category, Subcategory, Product, ProductVariant, ProductImage, Review, ReviewImage, Comment, CommentReply

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 5

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'subcategory')
    inlines = [ProductVariantInline, ProductImageInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'price', 'discount', 'stock')

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    inlines = [ReviewImageInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'content', 'created_at')

@admin.register(CommentReply)
class CommentReplyAdmin(admin.ModelAdmin):
    list_display = ('comment', 'user', 'content', 'created_at')
