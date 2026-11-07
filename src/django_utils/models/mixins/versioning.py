from dirtyfields import DirtyFieldsMixin
from django.db import models

__all__ = [
    "VersionFieldMixin",
    "AutoVersionFieldMixin",
]


class VersionFieldMixin(models.Model):
    version = models.PositiveIntegerField(default=1, editable=False)

    class Meta:
        abstract = True


class AutoVersionFieldMixin(DirtyFieldsMixin, VersionFieldMixin):
    """Increment ``version`` on save whenever another field has changed."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk:
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            dirty_fields.pop("version", None)
            if dirty_fields:
                self.version += 1

        super().save(*args, **kwargs)
