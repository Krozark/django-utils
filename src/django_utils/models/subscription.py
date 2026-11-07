from django.contrib.auth.models import Group, Permission
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

__all__ = [
    "AbstractSubscriptionPlan",
]


class AbstractSubscriptionPlan(models.Model):
    """A plan granting permissions to the users subscribed to it, through Django groups and permissions.

    Add the limits and the features of your own plans in the concrete model. The permissions of a plan are
    given to users by a backend (see ``ExtraPermissionsBackend``) using ``get_permissions()``.
    """

    name = models.CharField(max_length=20, unique=True, help_text=_("Subscription plan"))
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="%(app_label)s_%(class)s_related",
        help_text=_("Django groups whose permissions are granted to users with active subscriptions"),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="%(app_label)s_%(class)s_related",
        help_text=_("Specific permissions granted to users with active subscriptions"),
    )
    description = models.TextField(blank=True, null=True, help_text=_("Description of the plan"))

    class Meta:
        abstract = True
        ordering = ["name"]
        verbose_name = _("Subscription plan")

    def __str__(self):
        return self.name

    def get_permissions(self):
        """Return the permissions granted by the plan: its own ones and the ones of its groups."""
        return Permission.objects.filter(Q(group__in=self.groups.all()) | Q(pk__in=self.user_permissions.all()))
