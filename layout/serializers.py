from rest_framework import serializers
from .models import Layout, LayoutSection, Image

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image_id', 'image']

class LayoutSectionSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    class Meta:
        model = LayoutSection
        fields = ['code', 'images']


class LayoutSerializer(serializers.ModelSerializer):
    layout_sections = LayoutSectionSerializer(many=True, read_only=True)
    class Meta:
        model = Layout
        fields = ['name', 'non_deletable', 'active']

