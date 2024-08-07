from rest_framework import serializers
from .models import Layout, LayoutSection, Image

class LayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layout
        fields = '__all__'

class LayoutSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayoutSection
        fields = '__all__'

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = '__all__'