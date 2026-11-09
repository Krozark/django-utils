from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from django_utils.management.base import CleanupCommand, DryRunCommand

from ..models import SoftDeletableItem


class CleanDeletedItems(CleanupCommand):
    stale_name = "deleted item"

    def get_queryset(self):
        return SoftDeletableItem.objects.filter(is_deleted=True)


class CountItems(DryRunCommand):
    def handle(self, *args, **options):
        self.stdout.write(f"dry_run={self.dry_run}")


def run(command, *args):
    out = StringIO()
    call_command(command, *args, stdout=out)
    return out.getvalue()


class DryRunCommandTests(TestCase):
    def test_dry_run_option(self):
        self.assertIn("dry_run=False", run(CountItems()))
        self.assertIn("dry_run=True", run(CountItems(), "--dry-run"))


class CleanupCommandTests(TestCase):
    def setUp(self):
        self.deleted = SoftDeletableItem.objects.create(is_deleted=True)
        self.kept = SoftDeletableItem.objects.create()

    def test_deletes_the_stale_objects(self):
        output = run(CleanDeletedItems())

        self.assertIn("Found 1 deleted item(s).", output)
        self.assertIn("Deleted 1 deleted item(s).", output)
        self.assertEqual(list(SoftDeletableItem.objects.all()), [self.kept])

    def test_dry_run_deletes_nothing(self):
        output = run(CleanDeletedItems(), "--dry-run")

        self.assertIn("Dry run complete", output)
        self.assertEqual(SoftDeletableItem.objects.count(), 2)

    def test_nothing_to_delete(self):
        self.deleted.delete()

        self.assertIn("No deleted items to delete.", run(CleanDeletedItems()))

    def test_plural_can_be_customized(self):
        class Command(CleanDeletedItems):
            stale_name = "mouse"
            stale_name_plural = "mice"

        SoftDeletableItem.objects.all().delete()
        self.assertIn("No mice to delete.", run(Command()))

    def test_get_queryset_is_required(self):
        with self.assertRaises(NotImplementedError):
            run(CleanupCommand())
