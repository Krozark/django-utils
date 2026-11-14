import django_filters
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
