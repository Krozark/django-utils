from django.test import SimpleTestCase as DjangoSimpleTestCase
from rest_framework.test import APIClient

from django_utils.testing import SimpleTestCase, TestCase
from tests.testing.factories import UserFactory


class TestCaseDefaultsTests(TestCase):
    def test_defaults(self):
        self.assertIsNone(self.maxDiff)
        self.assertIsInstance(self.client, APIClient)


USERS = {
    "anonymous": None,
    "admin": lambda: UserFactory(username="admin", is_staff=True),
    "plain": UserFactory.build(username="plain"),
}


class UsersTests(TestCase):
    users = USERS

    def test_callables_are_resolved_once_per_class(self):
        self.assertIsNone(self.users["anonymous"])
        self.assertTrue(self.users["admin"].is_staff)
        self.assertIsNotNone(self.users["admin"].pk)

    def test_instances_are_kept_as_is(self):
        self.assertEqual(self.users["plain"].username, "plain")

    def test_class_declaration_is_not_mutated(self):
        self.assertTrue(callable(USERS["admin"]))

    def test_get_user(self):
        self.assertIsNone(self.get_user("anonymous"))
        self.assertTrue(self.get_user("admin").is_staff)

    def test_get_user_unknown_key(self):
        with self.assertRaisesMessage(KeyError, "ghost"):
            self.get_user("ghost")


class SimpleTestCaseTests(DjangoSimpleTestCase):
    def test_is_database_free(self):
        self.assertEqual(SimpleTestCase.databases, set())
        self.assertIsNone(SimpleTestCase.maxDiff)
