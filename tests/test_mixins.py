from datetime import UTC, datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import models
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps
from django.utils import translation

from django_utils.models import ClassRegistryMixin, PermissionCacheMixin

from .models import (
    AbstractShape,
    Animal,
    Circle,
    Dog,
    OwnedItem,
    PublicItem,
    SizedItem,
    SoftDeletableItem,
    Square,
    UUIDItem,
    UUIDVersionedItem,
    VersionedItem,
)


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

    def test_a_new_object_with_a_known_primary_key_starts_at_one(self):
        self.assertEqual(UUIDVersionedItem.objects.create(name="a").version, 1)

    def test_save_with_update_fields_persists_the_new_version(self):
        self.item.name = "b"
        self.item.save(update_fields=["name"])
        self.item.refresh_from_db()
        self.assertEqual(self.item.version, 2)

    def test_changes_outside_update_fields_do_not_increment(self):
        self.item.name = "b"
        self.item.save(update_fields=[])
        self.item.refresh_from_db()
        self.assertEqual(self.item.version, 1)

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

    def test_created_at_display_uses_the_local_time_and_the_language(self):
        item = OwnedItem.objects.create(created_by=self.user)
        item.created_at = datetime(2026, 11, 7, 8, 30, tzinfo=UTC)

        with self.settings(TIME_ZONE="Asia/Tokyo"):
            with translation.override("fr"):
                self.assertEqual(item.get_created_at_display(), "07/11/2026 17:30")
            with translation.override("en"):
                self.assertEqual(item.get_created_at_display(), "11/07/2026 5:30 p.m.")

    def test_created_at_display_format_can_be_customized(self):
        item = OwnedItem(created_at=datetime(2026, 11, 7, 8, 30, tzinfo=UTC))
        item.created_at_display_format = "Y-m-d"

        with self.settings(TIME_ZONE="UTC"):
            self.assertEqual(item.get_created_at_display(), "2026-11-07")


class SoftDeletionMixinTests(TestCase):
    def setUp(self):
        self.item = SoftDeletableItem.objects.create()

    def test_schedule_deletion(self):
        self.item.schedule_deletion(grace_days=10)
        self.item.refresh_from_db()

        self.assertTrue(self.item.is_deleted)
        self.assertEqual(self.item.deletion_scheduled_for - self.item.deleted_at, timedelta(days=10))

    def test_get_expired_returns_objects_past_their_grace_period(self):
        expired = SoftDeletableItem.objects.create()
        expired.schedule_deletion(grace_days=-1)
        self.item.schedule_deletion(grace_days=10)
        SoftDeletableItem.objects.create()  # not deleted

        self.assertEqual(list(SoftDeletableItem.get_expired()), [expired])

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

    def test_update_fields_none_saves_every_field(self):
        item = SizedItem.objects.create(content="hello")
        item.content = "hello world"
        item.save(update_fields=None)
        item.refresh_from_db()
        self.assertEqual((item.content, item.storage_size), ("hello world", 11))

    def test_human_readable_size(self):
        self.assertEqual(SizedItem(storage_size=2048).get_storage_size(), "2.0\xa0KB")


class UUIDMixinTests(TestCase):
    def test_uuid_is_unique_and_generated(self):
        self.assertNotEqual(UUIDItem.objects.create().uuid, UUIDItem.objects.create().uuid)


class ClassRegistryMixinTests(SimpleTestCase):
    def test_concrete_subclasses_of_an_abstract_root_register(self):
        self.assertEqual(AbstractShape.get_registry(), {"Circle": Circle, "Square": Square})

    def test_abstract_intermediate_classes_do_not_register(self):
        self.assertNotIn("AbstractPolygon", AbstractShape.get_registry())

    def test_a_concrete_root_does_not_register_itself(self):
        self.assertEqual(Animal.get_registry(), {"Dog": Dog})

    def test_hierarchies_do_not_share_a_registry(self):
        self.assertIsNot(AbstractShape.get_registry(), Animal.get_registry())

    @isolate_apps("tests")
    def test_missing_get_registry_override_raises_immediately(self):
        class IncompleteRoot(ClassRegistryMixin, models.Model):
            class Meta:
                abstract = True
                app_label = "tests"

        with self.assertRaises(NotImplementedError):

            class Concrete(IncompleteRoot):
                class Meta:
                    app_label = "tests"


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
