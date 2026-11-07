from django.db import models

__all__ = [
    "IsPublicFilteredManager",
    "IsPublicMixin",
]


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
