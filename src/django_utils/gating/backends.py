from django.contrib.auth.backends import ModelBackend

__all__ = [
    "ExtraPermissionsBackend",
]


class ExtraPermissionsBackend(ModelBackend):
    """``ModelBackend`` that grants permissions coming from somewhere else than the user and its groups.

    Subclass it and implement ``get_extra_permissions()``, e.g. to grant the permissions of the plan a user
    has subscribed to while the subscription is active::

        class SubscriptionBackend(ExtraPermissionsBackend):
            def get_extra_permissions(self, user_obj):
                if not user_obj.subscription.is_active:
                    return None
                return Permission.objects.filter(group__in=user_obj.subscription.plan.groups.all())
    """

    def get_extra_permissions(self, user_obj):
        """Return a ``Permission`` queryset to grant to ``user_obj``, or ``None``."""
        return None

    def _get_user_permissions(self, user_obj):
        permissions = super()._get_user_permissions(user_obj)
        extra_permissions = self.get_extra_permissions(user_obj)
        return permissions if extra_permissions is None else permissions | extra_permissions
