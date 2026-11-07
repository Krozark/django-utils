import uuid

from django.db import models

__all__ = [
    "UUIDMixin",
]


class UUIDMixin(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True
