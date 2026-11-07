from django.db import models
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

__all__ = [
    "StorageSizeMixin",
]


class StorageSizeMixin(models.Model):
    """Mixin for models that occupy storage space and need their size tracked.

    Subclasses must implement ``update_size()`` to compute and assign
    ``storage_size`` from the model's own file fields before each save.
    """

    storage_size = models.PositiveBigIntegerField(
        default=0,
        editable=False,
        help_text=_("Size in bytes"),
    )

    class Meta:
        abstract = True

    def update_size(self):
        """Compute and assign storage_size. Must be implemented by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement update_size()")

    def get_storage_size(self):
        """Return human-readable file size."""
        return filesizeformat(self.storage_size)

    def save(self, *args, **kwargs):
        self.update_size()
        if "update_fields" in kwargs:
            update_fields = list(kwargs["update_fields"])
            if "storage_size" not in update_fields:
                update_fields.append("storage_size")
            kwargs["update_fields"] = update_fields
        super().save(*args, **kwargs)
