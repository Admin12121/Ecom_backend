from rest_framework import serializers
from .models import Layout, Image, Link, Title

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ['id','link']

class TitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id','title']

class ImageSerializer(serializers.ModelSerializer):
    links = LinkSerializer(many=True, read_only=True, source='link_set')
    titles = TitleSerializer(many=True, read_only=True, source='title_set')
    class Meta:
        model = Image
        fields = ['image_id', 'image', 'links', 'titles', 'link_no', 'title_no']

class LayoutSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True, source='image_set')
    class Meta:
        model = Layout
        fields = ['name', 'layout_slug', 'non_deletable', 'active', 'images', 'no_image']