from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from django_utils.models import ClassRegistryMixin, PermissionCacheMixin

from .models import OwnedItem, PublicItem, SizedItem, SoftDeletableItem, UUIDItem, VersionedItem


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


class IsPublicMixinTests(TestCase):
    def test_manager_public_only_returns_public_objects(self):
        PublicItem.objects.create(is_public=False)
        public = PublicItem.objects.create(is_public=True)

        self.assertEqual(PublicItem.objects.count(), 2)
        self.assertEqual(list(PublicItem.manager_public.all()), [public])


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


class UUIDMixinTests(TestCase):
    def test_uuid_is_unique_and_generated(self):
        self.assertNotEqual(UUIDItem.objects.create().uuid, UUIDItem.objects.create().uuid)


class _FakeMeta:
    def __init__(self, abstract):
        self.abstract = abstract


def _make_root():
    """A minimal, correctly-configured ClassRegistryMixin root."""

    class Root(ClassRegistryMixin):
        _meta = _FakeMeta(abstract=True)
        _registry = {}

        @classmethod
        def get_registry(cls):
            return cls._registry

        @classmethod
        def _registry_key(cls):
            return cls.__name__

    return Root


class ClassRegistryMixinTests(SimpleTestCase):
    """Plain fake ``_meta`` stand-ins are used: the mixin only ever reads ``cls._meta.abstract``."""

    def test_concrete_subclass_self_registers(self):
        Root = _make_root()

        class Concrete(Root):
            _meta = _FakeMeta(abstract=False)

        self.assertEqual(Root._registry, {"Concrete": Concrete})

    def test_abstract_subclass_does_not_register(self):
        Root = _make_root()

        class StillAbstract(Root):
            _meta = _FakeMeta(abstract=True)

        self.assertEqual(Root._registry, {})

    def test_two_hierarchies_do_not_share_a_registry(self):
        RootA = _make_root()
        RootB = _make_root()

        class ConcreteA(RootA):
            _meta = _FakeMeta(abstract=False)

        class ConcreteB(RootB):
            _meta = _FakeMeta(abstract=False)

        self.assertEqual(RootA._registry, {"ConcreteA": ConcreteA})
        self.assertEqual(RootB._registry, {"ConcreteB": ConcreteB})

    def test_missing_get_registry_override_raises_immediately(self):
        class IncompleteRoot(ClassRegistryMixin):
            _meta = _FakeMeta(abstract=True)

        with self.assertRaises(NotImplementedError):

            class Concrete(IncompleteRoot):
                _meta = _FakeMeta(abstract=False)


class PermissionCacheMixinTests(TestCase):
    def test_clear_permission_cache_forgets_the_cached_permissions(self):
        class User(PermissionCacheMixin):
            pass

        user = User()
        user._perm_cache = user._user_perm_cache = user._group_perm_cache = set()
        user.other = "kept"

        user.clear_permission_cache()

        self.assertEqual(vars(user), {"other": "kept"})

    def test_clear_permission_cache_without_cache_is_a_no_op(self):
        PermissionCacheMixin().clear_permission_cache()

    def test_permissions_are_checked_again_after_clearing(self):
        class CachedUser(PermissionCacheMixin, get_user_model()):
            class Meta:
                proxy = True
                app_label = "tests"

        user = CachedUser.objects.create_user(username="cached")
        self.assertFalse(user.has_perm("tests.add_owneditem"))

        user.user_permissions.add(Permission.objects.get(codename="add_owneditem"))
        self.assertFalse(user.has_perm("tests.add_owneditem"))  # still cached

        user.clear_permission_cache()
        self.assertTrue(user.has_perm("tests.add_owneditem"))
