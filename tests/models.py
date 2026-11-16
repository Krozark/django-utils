import uuid

from django.core.files.storage import InMemoryStorage
from django.db import models
from django.db.models import Lookup
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
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

    class Meta:
        abstract = True


class AbstractPolygon(AbstractShape):
    class Meta:
        abstract = True


class Circle(AbstractShape):
    pass


class Square(AbstractPolygon):
    pass


class Animal(ClassRegistryMixin, models.Model):
    """Concrete registry root: only its subclasses are registered."""


class Dog(Animal):
    pass


class OwnedPublicItem(CreatedByMixin, IsPublicMixin):
    pass


class ContractItemQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class ContractItemManager(models.Manager.from_queryset(ContractItemQuerySet)):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class ContractItem(models.Model):
    """Model exercising every aspect checked by the model/manager contract test cases."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    objects = ContractItemManager()

    class Meta:
        verbose_name = _("contract item")
        verbose_name_plural = _("contract items")
        constraints = [
            models.CheckConstraint(condition=models.Q(slug__gt=""), name="tests__contractitem__slug_not_empty")
        ]

    def __str__(self):
        return self.title

    def natural_key(self):
        return (self.slug,)

    def get_upper_title(self):
        return self.title.upper()

    @property
    def upper_title(self):
        return self.get_upper_title()

    def get_lower_title(self):
        return self.title.lower()

    @cached_property
    def lower_title(self):
        return self.get_lower_title()


class TagField(models.CharField):
    """CharField with an extra ``ne`` lookup."""


@TagField.register_lookup
class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} <> {rhs}", [*lhs_params, *rhs_params]


class TaggedItem(models.Model):
    tag = TagField(max_length=20)
