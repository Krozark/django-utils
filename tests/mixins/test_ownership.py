from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ..models import OwnedItem


class CreatedByMixinTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="john")

    def test_get_or_create_for_user_is_idempotent(self):
        first = OwnedItem.get_or_create_for_user(self.user)
        second = OwnedItem.get_or_create_for_user(self.user)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.created_by, self.user)

    def test_created_at_display_uses_local_time(self):
        item = OwnedItem.objects.create(created_by=self.user)

        with self.settings(TIME_ZONE="Asia/Tokyo"):
            expected = timezone.localtime(item.created_at).strftime("%d/%m/%Y %H:%M")
            self.assertEqual(item.get_created_at_display(), expected)
