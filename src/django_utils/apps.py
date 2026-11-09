from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

__all__ = ["DjangoUtilsConfig"]


class DjangoUtilsConfig(AppConfig):
    name = "django_utils"
    verbose_name = _("Django utils")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from .gating import checks  # noqa: F401  (registers the system checks)
