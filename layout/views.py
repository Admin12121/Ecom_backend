from rest_framework import viewsets
from .models import Layout, LayoutSection, Image
from .serializers import LayoutSerializer, LayoutSectionSerializer, ImageSerializer

class LayoutViewSet(viewsets.ModelViewSet):
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer

class LayoutSectionViewSet(viewsets.ModelViewSet):
    queryset = LayoutSection.objects.all()
    serializer_class = LayoutSectionSerializer

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer