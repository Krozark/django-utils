from django.contrib.auth.models import Permission
from django.test import TestCase

from django_utils.gating import get_gated_features, get_user_gated_features, perm_codename

from ..helpers import create_user


class RegistryTests(TestCase):
    def setUp(self):
        get_gated_features.cache_clear()

    def test_perm_codename(self):
        self.assertEqual(perm_codename("app.set_on_start"), "set_on_start")

    def test_gated_features_are_discovered_without_duplicates(self):
        self.assertEqual(get_gated_features(), (("use_secret", "tests.use_secret"),))

    def test_user_gated_features(self):
        user = create_user()
        self.assertEqual(get_user_gated_features(user), {"use_secret": False})

        user.user_permissions.add(Permission.objects.get(codename="use_secret"))
        user = type(user).objects.get(pk=user.pk)  # drop the permission cache
        self.assertEqual(get_user_gated_features(user), {"use_secret": True})

    def test_superuser_has_every_gated_feature(self):
        self.assertEqual(get_user_gated_features(create_user(is_superuser=True)), {"use_secret": True})
