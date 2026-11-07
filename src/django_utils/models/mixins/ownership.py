from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

__all__ = [
    "CreatedByMixin",
]


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

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create an instance for the given user."""
        obj, _created = cls.objects.get_or_create(created_by=user)
        return obj

    def get_created_at_display(self):
        """Return the creation date formatted in the current time zone."""
        created_at = timezone.localtime(self.created_at) if timezone.is_aware(self.created_at) else self.created_at
        return created_at.strftime("%d/%m/%Y %H:%M")
