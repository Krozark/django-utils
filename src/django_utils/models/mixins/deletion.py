from datetime import timedelta

from django.db import models
from django.utils import timezone

__all__ = [
    "SoftDeletionMixin",
]


class SoftDeletionMixin(models.Model):
    """Mixin for soft-deleting models with a grace period before hard deletion."""

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deletion_scheduled_for = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def schedule_deletion(self, grace_days=30):
        """Mark as deleted and schedule hard deletion after grace_days."""
        now = timezone.now()
        self.is_deleted = True
        self.deleted_at = now
        self.deletion_scheduled_for = now + timedelta(days=grace_days)
        self.save()

    def cancel_deletion(self):
        """Cancel a scheduled deletion."""
        self.is_deleted = False
        self.deleted_at = None
        self.deletion_scheduled_for = None
        self.save()
