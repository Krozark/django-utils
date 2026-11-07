from datetime import timedelta

from django.test import TestCase

from ..models import SoftDeletableItem


class SoftDeletionMixinTests(TestCase):
    def setUp(self):
        self.item = SoftDeletableItem.objects.create()

    def test_schedule_deletion(self):
        self.item.schedule_deletion(grace_days=10)
        self.item.refresh_from_db()

        self.assertTrue(self.item.is_deleted)
        self.assertEqual(self.item.deletion_scheduled_for - self.item.deleted_at, timedelta(days=10))

    def test_cancel_deletion(self):
        self.item.schedule_deletion()
        self.item.cancel_deletion()
        self.item.refresh_from_db()

        self.assertFalse(self.item.is_deleted)
        self.assertIsNone(self.item.deleted_at)
        self.assertIsNone(self.item.deletion_scheduled_for)
