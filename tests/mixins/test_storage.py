from django.test import TestCase

from ..models import SizedItem


class StorageSizeMixinTests(TestCase):
    def test_size_is_updated_on_save(self):
        item = SizedItem.objects.create(content="hello")
        self.assertEqual(item.storage_size, 5)

    def test_size_is_saved_with_update_fields(self):
        item = SizedItem.objects.create(content="hello")
        item.content = "hello world"
        item.save(update_fields=["content"])
        item.refresh_from_db()
        self.assertEqual(item.storage_size, 11)

    def test_human_readable_size(self):
        self.assertEqual(SizedItem(storage_size=2048).get_storage_size(), "2.0\xa0KB")
