from django.test import TestCase

from ..models import VersionedItem


class AutoVersionFieldMixinTests(TestCase):
    def setUp(self):
        self.item = VersionedItem.objects.create(name="a")

    def test_starts_at_one(self):
        self.assertEqual(self.item.version, 1)

    def test_increments_when_a_field_changes(self):
        self.item.name = "b"
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.version, 2)

    def test_unchanged_save_does_not_increment(self):
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.version, 1)
