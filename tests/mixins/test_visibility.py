from django.test import TestCase

from ..models import PublicItem


class IsPublicMixinTests(TestCase):
    def test_manager_public_only_returns_public_objects(self):
        PublicItem.objects.create(is_public=False)
        public = PublicItem.objects.create(is_public=True)

        self.assertEqual(PublicItem.objects.count(), 2)
        self.assertEqual(list(PublicItem.manager_public.all()), [public])
