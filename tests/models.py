from django.core.files.storage import InMemoryStorage
from django.db import models
from private_storage.fields import PrivateFileField

from django_utils.models import (
    AbstractSubscriptionPlan,
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


class FileItem(models.Model):
    file = models.FileField(storage=InMemoryStorage(), blank=True)


class GatedItem(models.Model):
    gated_features = ["tests.use_secret"]

    name = models.CharField(max_length=50, blank=True)
    secret = models.CharField(max_length=50, blank=True)

    class Meta:
        permissions = [("use_secret", "Can use the secret")]


class GatedChildItem(GatedItem):
    """Inherits ``gated_features``, which must not be listed twice."""


class Plan(AbstractSubscriptionPlan):
    pass


class OtherPlan(AbstractSubscriptionPlan):
    """A second concrete plan model must not clash with the first one."""


class PrivateFileItem(models.Model):
    file = PrivateFileField(upload_to="items", blank=True)
