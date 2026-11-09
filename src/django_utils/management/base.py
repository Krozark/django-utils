import logging

from django.core.management.base import BaseCommand

__all__ = [
    "CleanupCommand",
    "DryRunCommand",
]

logger = logging.getLogger(__name__)


class DryRunCommand(BaseCommand):
    """Command with a ``--dry-run`` option: when ``self.dry_run`` is true, nothing must be changed."""

    dry_run = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )

    def execute(self, *args, **options):
        self.dry_run = options["dry_run"]
        return super().execute(*args, **options)


class CleanupCommand(DryRunCommand):
    """Delete the stale objects returned by ``get_queryset()``, reporting what was done.

    Usage::

        class Command(CleanupCommand):
            help = "Delete expired tokens."
            stale_name = "expired token"

            def get_queryset(self):
                return Token.objects.filter(expires_at__lte=timezone.now())
    """

    #: Singular description of the objects to delete, used in the messages.
    stale_name = "stale object"
    #: Plural description; defaults to ``stale_name`` + "s".
    stale_name_plural = None

    def get_queryset(self):
        raise NotImplementedError

    def handle(self, *args, **options):
        stale_objects = self.get_queryset()
        count = stale_objects.count()

        if count == 0:
            self.stdout.write(f"No {self.stale_name_plural or self.stale_name + 's'} to delete.")
            return

        self.stdout.write(f"Found {count} {self.stale_name}(s).")

        if self.dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. No changes were made."))
        else:
            stale_objects.delete()
            logger.info("Deleted %d %s(s).", count, self.stale_name)
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} {self.stale_name}(s)."))
