import factory
from django.contrib.auth import get_user_model
from django.test import TestCase
from factory.errors import FactoryError

from django_utils.testing.factories import CreatedByMixinFactory, IsPublicMixinFactory, UserFactory
from tests.models import OwnedItem, OwnedPublicItem, PublicItem


class PublicItemFactory(IsPublicMixinFactory):
    class Meta:
        model = PublicItem


class OwnedItemFactory(CreatedByMixinFactory):
    class Meta:
        model = OwnedItem


class OwnedPublicItemFactory(IsPublicMixinFactory, CreatedByMixinFactory):
    class Meta:
        model = OwnedPublicItem


class UserFactoryTests(TestCase):
    def test_creates_distinct_saved_users(self):
        first, second = UserFactory(), UserFactory()

        self.assertIsInstance(first, get_user_model())
        self.assertIsNotNone(first.pk)
        self.assertNotEqual(first.username, second.username)
        self.assertEqual(first.email, f"{first.username}@example.com")
        self.assertEqual((first.is_active, first.is_staff, first.is_superuser), (True, False, False))

    def test_build_does_not_save(self):
        self.assertIsNone(UserFactory.build().pk)

    def test_attributes_can_be_overridden(self):
        user = UserFactory(username="admin", is_staff=True)

        self.assertEqual((user.username, user.is_staff, user.email), ("admin", True, "admin@example.com"))


class IsPublicMixinFactoryTests(TestCase):
    def test_is_abstract(self):
        with self.assertRaises(FactoryError):
            IsPublicMixinFactory()

    def test_is_public_is_a_boolean(self):
        self.assertIsInstance(PublicItemFactory().is_public, bool)

    def test_is_public_can_be_overridden(self):
        self.assertTrue(PublicItemFactory(is_public=True).is_public)
        self.assertFalse(PublicItemFactory(is_public=False).is_public)

    def test_declaration_is_random(self):
        self.assertIsInstance(IsPublicMixinFactory._meta.pre_declarations.as_dict()["is_public"], factory.Faker)


class CreatedByMixinFactoryTests(TestCase):
    def test_is_abstract(self):
        with self.assertRaises(FactoryError):
            CreatedByMixinFactory()

    def test_creates_one_user_per_object(self):
        first, second = OwnedItemFactory(), OwnedItemFactory()

        self.assertIsInstance(first.created_by, get_user_model())
        self.assertNotEqual(first.created_by, second.created_by)

    def test_created_by_can_be_overridden(self):
        user = UserFactory()

        self.assertEqual(OwnedItemFactory(created_by=user).created_by, user)

    def test_combines_with_the_public_flag(self):
        item = OwnedPublicItemFactory(is_public=True)

        self.assertTrue(item.is_public)
        self.assertIsNotNone(item.created_by.pk)
