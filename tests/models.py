import uuid

from django.core.files.storage import InMemoryStorage
from django.db import models
from private_storage.fields import PrivateFileField

from django_utils.models import (
    AbstractSubscriptionPlan,
    AutoVersionFieldMixin,
    ClassRegistryMixin,
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


class UUIDVersionedItem(AutoVersionFieldMixin):
    """A primary key known before the first save: the object must still start at version 1."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=50)


class AbstractShape(ClassRegistryMixin, models.Model):
    """Abstract registry root."""

    _class_registry = {}

    class Meta:
        abstract = True

    @classmethod
    def get_registry(cls):
        return cls._class_registry

    @classmethod
    def _registry_key(cls):
        return cls.__name__


class AbstractPolygon(AbstractShape):
    class Meta:
        abstract = True


class Circle(AbstractShape):
    pass


class Square(AbstractPolygon):
    pass


class Animal(ClassRegistryMixin, models.Model):
    """Concrete registry root: only its subclasses are registered."""

    _class_registry = {}

    @classmethod
    def get_registry(cls):
        return cls._class_registry

    @classmethod
    def _registry_key(cls):
        return cls.__name__


class Dog(Animal):
    pass


class OwnedPublicItem(CreatedByMixin, IsPublicMixin):
    pass
