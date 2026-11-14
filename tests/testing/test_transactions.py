from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django_utils.testing.transactions import rollback_atomic

from tests.models import VersionedItem


class RollbackAtomicTests(TestCase):
    def test_changes_are_rolled_back(self):
        with rollback_atomic():
            VersionedItem.objects.create(name="a")
            self.assertEqual(VersionedItem.objects.count(), 1)
        self.assertEqual(VersionedItem.objects.count(), 0)

    def test_exception_propagates_and_rolls_back(self):
        with self.assertRaises(ValueError), rollback_atomic():
            VersionedItem.objects.create(name="a")
            raise ValueError
        self.assertEqual(VersionedItem.objects.count(), 0)

    def test_database_error_does_not_break_outer_transaction(self):
        with self.assertRaises(IntegrityError), rollback_atomic():
            VersionedItem.objects.create(name=None)
        self.assertEqual(VersionedItem.objects.count(), 0)

    def test_explicit_aliases(self):
        with rollback_atomic(["default"]):
            VersionedItem.objects.create(name="a")
        self.assertEqual(VersionedItem.objects.count(), 0)


class RollbackAtomicWithoutDatabaseTests(SimpleTestCase):
    def test_no_aliases_is_a_noop(self):
        with rollback_atomic([]):
            pass
