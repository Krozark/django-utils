import uuid
from datetime import timedelta

from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

__all__ = [
    "VersionFieldMixin",
    "AutoVersionFieldMixin",
    "IsPublicFilteredManager",
    "IsPublicMixin",
    "CreatedByMixin",
    "SoftDeletionMixin",
    "StorageSizeMixin",
    "UUIDMixin",
    "ClassRegistryMixin",
    "PermissionCacheMixin",
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
        if not self._state.adding:
            update_fields = kwargs.get("update_fields")
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            dirty_fields.pop("version", None)
            if update_fields is not None:
                dirty_fields = {name: value for name, value in dirty_fields.items() if name in update_fields}
            if dirty_fields:
                self.version += 1
                if update_fields is not None:
                    kwargs["update_fields"] = {*update_fields, "version"}

        super().save(*args, **kwargs)


class IsPublicFilteredManager(models.Manager):
    """Manager that filters queryset to only return public objects."""

    def get_queryset(self):
        return super().get_queryset().filter(is_public=True)


class IsPublicMixin(models.Model):
    """Mixin to add is_public field with filtered manager.

    Managers:
        objects: Default manager (returns all objects)
        manager_public: Only returns objects where is_public=True
    """

    is_public = models.BooleanField(default=False)

    objects = models.Manager()  # Default: returns ALL objects
    manager_public = IsPublicFilteredManager()

    class Meta:
        abstract = True


class CreatedByMixin(models.Model):
    """Mixin to track who created an object and when."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name=_("Created by"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))

    #: Format of ``get_created_at_display()``: a Django format name (localized) or a format string.
    created_at_display_format = "SHORT_DATETIME_FORMAT"

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create an instance for the given user."""
        obj, _created = cls._default_manager.get_or_create(created_by=user)
        return obj

    def get_created_at_display(self):
        """Return the creation date, in the current time zone and language."""
        created_at = timezone.localtime(self.created_at) if timezone.is_aware(self.created_at) else self.created_at
        return date_format(created_at, self.created_at_display_format)


class SoftDeletionMixin(models.Model):
    """Mixin for soft-deleting models with a grace period before hard deletion."""

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deletion_scheduled_for = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @classmethod
    def get_expired(cls):
        """Return the objects whose grace period is over: they can now be hard-deleted."""
        return cls._default_manager.filter(is_deleted=True, deletion_scheduled_for__lte=timezone.now())

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
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = {*update_fields, "storage_size"}
        super().save(*args, **kwargs)


class UUIDMixin(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class ClassRegistryMixin:
    """Self-registers every concrete subclass into a dict keyed by `_registry_key()`.

    Factors out the self-registration pattern: every concrete model (as opposed to an abstract one)
    inheriting from the class holding the registry adds itself to it, so a dispatcher can later resolve
    `some_string -> the right subclass` without a hand-written if/elif chain.

    The class inheriting directly from this mixin is the root of a hierarchy and gets its own registry,
    created automatically: hierarchies never share a dict. The root is either abstract or concrete; a concrete
    root is not registered itself, only its subclasses are.

    Usage::

        class Shape(ClassRegistryMixin, models.Model):

            class Meta:
                abstract = True

            @classmethod
            def _registry_key(cls) -> str:
                return cls.__name__  # default, override to register under another key
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if ClassRegistryMixin in cls.__bases__:
            cls._class_registry = {}

    @classmethod
    def get_registry(cls) -> dict:
        """Return THIS hierarchy's registry dict."""
        if not hasattr(cls, "_class_registry"):
            raise TypeError(f"{cls.__name__} is not part of a registry hierarchy.")
        return cls._class_registry

    @classmethod
    def _registry_key(cls) -> str:
        """Return the key this concrete subclass registers itself under."""
        return cls.__name__

    @classmethod
    def _register(cls) -> None:
        """Add this concrete subclass to its hierarchy's registry."""
        cls.get_registry()[cls._registry_key()] = cls


@receiver(class_prepared)
def _register_class(sender, **kwargs):
    # Sent for concrete models only (never for abstract ones), once their ``_meta`` is complete.
    # The historical models rendered by the migrations (module "__fake__") have no methods: ignore them.
    if sender.__module__ == "__fake__" or not issubclass(sender, ClassRegistryMixin):
        return
    if "_class_registry" not in vars(sender):  # a root does not register itself
        sender._register()


class PermissionCacheMixin:
    """Mixin for user models: forget the permissions Django cached on the instance.

    ``ModelBackend`` caches the permissions on the user object the first time they are checked. When they
    change (e.g. a subscription is activated), call ``clear_permission_cache()`` so that the next check
    reflects the current state.
    """

    PERMISSION_CACHE_ATTRIBUTES = ("_perm_cache", "_user_perm_cache", "_group_perm_cache")

    def clear_permission_cache(self):
        for attribute in self.PERMISSION_CACHE_ATTRIBUTES:
            self.__dict__.pop(attribute, None)
