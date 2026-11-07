from django.db import models

from django_utils.models import (
    AutoVersionFieldMixin,
    CreatedByMixin,
    IsPublicMixin,
    SoftDeletionMixin,
    StorageSizeMixin,
    UUIDMixin,
)


class VersionedItem(AutoVersionFieldMixin):
    name = models.CharField(max_length=50)


class PublicItem(IsPublicMixin):
    pass


class OwnedItem(CreatedByMixin):
    pass


class SoftDeletableItem(SoftDeletionMixin):
    pass


class SizedItem(StorageSizeMixin):
    content = models.TextField(default="")

    def update_size(self):
        self.storage_size = len(self.content)


class UUIDItem(UUIDMixin):
    pass


class OwnedUUIDItem(UUIDMixin, CreatedByMixin):
    pass
