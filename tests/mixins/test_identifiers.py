from django.test import TestCase

from ..models import UUIDItem


class UUIDMixinTests(TestCase):
    def test_uuid_is_unique_and_generated(self):
        self.assertNotEqual(UUIDItem.objects.create().uuid, UUIDItem.objects.create().uuid)
