from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Layout, Image, Link, Title
from rest_framework.permissions import IsAuthenticated
from .serializers import LayoutSerializer, ImageSerializer, LinkSerializer, TitleSerializer
from django.shortcuts import get_object_or_404

class LayoutViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer

    def get_object(self):
        layout_slug = self.kwargs.get('layout_slug')
        data = get_object_or_404(Layout, layout_slug=layout_slug)
        print(layout_slug, data)

        return get_object_or_404(Layout, layout_slug=layout_slug)

    def create(self, request, *args, **kwargs):
        layout_data = request.data

        if layout_data.get('active', False):
            Layout.objects.filter(active=True).update(active=False)

        images_data = layout_data.pop('images', [])
        layout = Layout.objects.create(**layout_data)

        for image_data in images_data:
            links_data = image_data.pop('links', [])
            titles_data = image_data.pop('titles', [])
            image = Image.objects.create(layout=layout, **image_data)

            for link_data in links_data:
                Link.objects.create(image=image, **link_data)

            for title_data in titles_data:
                Title.objects.create(image=image, **title_data)

        serializer = self.get_serializer(layout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        layout_slug = kwargs.get('layout_slug')  # Ensure 'layout_slug' is accessed correctly
        layout = get_object_or_404(self.queryset, layout_slug=layout_slug)
        layout_data = request.data.dict()
        print(layout_data)

        if layout_data.get('active', False):
            Layout.objects.filter(active=True).exclude(pk=layout.pk).update(active=False)

        images_data = []
        for key, file in request.FILES.items():
            if key.startswith('images'):
                images_data.append({'image': file})

        for attr, value in layout_data.items():
            setattr(layout, attr, value)
        layout.save()

        layout.image_set.all().delete()

        for image_data in images_data:
            image = Image.objects.create(layout=layout, **image_data)

        serializer = self.get_serializer(layout)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        layout = self.get_object()
        print(layout)        
        if request.user.role != 'Admin':
            return Response({'detail': 'Unauthorized User'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(layout)
        return Response(serializer.data)