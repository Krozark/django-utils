from django.contrib.auth.models import Permission
from django.test import TestCase

from django_utils.gating.backends import ExtraPermissionsBackend

from ..helpers import create_user


class GrantBackend(ExtraPermissionsBackend):
    def get_extra_permissions(self, user_obj):
        return Permission.objects.filter(codename="use_secret")


class ExtraPermissionsBackendTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_without_hook_it_behaves_like_the_model_backend(self):
        backend = ExtraPermissionsBackend()
        self.assertFalse(backend.has_perm(self.user, "tests.use_secret"))

        self.user.user_permissions.add(Permission.objects.get(codename="use_secret"))
        self.assertTrue(backend.has_perm(type(self.user).objects.get(pk=self.user.pk), "tests.use_secret"))

    def test_extra_permissions_are_granted(self):
        self.assertTrue(GrantBackend().has_perm(self.user, "tests.use_secret"))
        self.assertFalse(GrantBackend().has_perm(self.user, "tests.add_gateditem"))

    def test_extra_permissions_are_added_to_the_user_ones(self):
        self.user.user_permissions.add(Permission.objects.get(codename="add_gateditem"))
        user = type(self.user).objects.get(pk=self.user.pk)

        self.assertEqual(GrantBackend().get_all_permissions(user), {"tests.use_secret", "tests.add_gateditem"})

    def test_inactive_users_get_nothing(self):
        self.user.is_active = False
        self.assertFalse(GrantBackend().has_perm(self.user, "tests.use_secret"))
