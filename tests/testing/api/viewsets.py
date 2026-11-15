import django_filters
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tests.models import ContractItem


class ContractItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractItem
        fields = ["id", "slug", "title", "is_active"]
        read_only_fields = ["id"]


class ContractItemFilterSet(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    title = django_filters.CharFilter(lookup_expr="icontains")
    min_id = django_filters.NumberFilter(field_name="id", lookup_expr="gte")

    class Meta:
        model = ContractItem
        fields = []


class ContractItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff sees every item, everybody else only the active ones."""

    serializer_class = ContractItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContractItemFilterSet
    lookup_field = "slug"

    def get_queryset(self):
        queryset = ContractItem.objects.order_by("title")
        if self.request.user.is_staff:
            return queryset
        return queryset.active()

    @action(detail=False, methods=["get"], url_path="titles")
    def titles(self, request):
        return Response(list(self.get_queryset().values_list("title", flat=True)))


class NPlusOneSerializer(serializers.ModelSerializer):
    """Runs one extra query per item: the number of queries grows with the number of items."""

    siblings = serializers.SerializerMethodField()

    class Meta:
        model = ContractItem
        fields = ["id", "siblings"]

    def get_siblings(self, obj):
        return ContractItem.objects.exclude(pk=obj.pk).count()


class NPlusOneViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NPlusOneSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    queryset = ContractItem.objects.order_by("pk")


class UserPermissionsViewSet(viewsets.ViewSet):
    """Reads the permissions of the user, which Django caches on the user instance."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(sorted(request.user.get_all_permissions()))


class ContentTypeViewSet(viewsets.ViewSet):
    """Reads a content type, which Django caches in the process after the first query."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(ContentType.objects.get_for_model(ContractItem).pk)
