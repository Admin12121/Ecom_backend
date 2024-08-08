from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Layout, LayoutSection, Image
from .serializers import LayoutSerializer, LayoutSectionSerializer, ImageSerializer

class LayoutViewSet(viewsets.ModelViewSet):
    queryset = Layout.objects.all()
    serializer_class = LayoutSerializer

    def create(self, request, *args, **kwargs):
        layout_data = request.data
        layout_sections_data = layout_data.pop('layout_sections', [])

        layout = Layout.objects.create(**layout_data)

        for section_data in layout_sections_data:
            images_data = section_data.pop('images', [])
            layout_section = LayoutSection.objects.create(layout=layout, **section_data)

            for image_data in images_data:
                Image.objects.create(layout_section=layout_section, **image_data)

        serializer = self.get_serializer(layout)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        layout = self.get_object()
        layout_data = request.data
        layout_sections_data = layout_data.pop('layout_sections', [])

        for attr, value in layout_data.items():
            setattr(layout, attr, value)
        layout.save()

        layout.layoutsection_set.all().delete()

        for section_data in layout_sections_data:
            images_data = section_data.pop('images', [])
            layout_section = LayoutSection.objects.create(layout=layout, **section_data)

            for image_data in images_data:
                Image.objects.create(layout_section=layout_section, **image_data)

        serializer = self.get_serializer(layout)
        return Response(serializer.data, status=status.HTTP_200_OK)