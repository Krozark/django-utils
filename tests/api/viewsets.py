from rest_framework import viewsets

from django_utils.api.serializers import CreatedByAndUUIDMixinSerializer
from django_utils.api.views import PrivateFileDownloaderMixin

from ..models import FileItem, OwnedUUIDItem


class OwnedUUIDItemSerializer(CreatedByAndUUIDMixinSerializer):
    class Meta(CreatedByAndUUIDMixinSerializer.Meta):
        model = OwnedUUIDItem


class OwnedUUIDItemViewSet(viewsets.ModelViewSet):
    queryset = OwnedUUIDItem.objects.order_by("pk")
    serializer_class = OwnedUUIDItemSerializer


class FileItemViewSet(PrivateFileDownloaderMixin, viewsets.ReadOnlyModelViewSet):
    queryset = FileItem.objects.all()
