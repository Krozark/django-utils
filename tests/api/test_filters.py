import uuid

from django.test import TestCase
from django_filters import FilterSet

from django_utils.api.filters import UUIDInFilter

from ..models import UUIDItem


class UUIDItemFilter(FilterSet):
    id = UUIDInFilter(field_name="uuid")

    class Meta:
        model = UUIDItem
        fields = ["id"]


class UUIDInFilterTests(TestCase):
    def setUp(self):
        self.items = [UUIDItem.objects.create() for _ in range(3)]

    def filtered(self, *uuids):
        return UUIDItemFilter({"id": ",".join(str(u) for u in uuids)}, UUIDItem.objects.all()).qs

    def test_filters_on_several_uuids(self):
        result = self.filtered(self.items[0].uuid, self.items[2].uuid)
        self.assertCountEqual(result, [self.items[0], self.items[2]])

    def test_unknown_uuid_matches_nothing(self):
        self.assertFalse(self.filtered(uuid.uuid4()).exists())
