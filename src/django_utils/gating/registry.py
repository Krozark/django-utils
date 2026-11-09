"""Registry of the gated features.

A gated feature is a Django permission (``"app_label.codename"``) that a project reserves for some users
(e.g. a subscription plan). Models declare theirs in a ``gated_features`` class attribute::

    class Ambience(models.Model):
        gated_features = ["my_app.set_on_start"]

        class Meta:
            permissions = [("set_on_start", "Can set the on_start of an ambience")]
"""

from functools import cache

from django.apps import apps
from django.contrib.auth import get_permission_codename

__all__ = [
    "get_declared_permissions",
    "get_gated_features",
    "get_user_gated_features",
    "iter_declared_gated_features",
    "iter_gated_features_declarations",
    "perm_codename",
]


def perm_codename(perm):
    """Return the codename of a permission string: ``"app_label.codename"`` -> ``"codename"``."""
    return perm.split(".", 1)[1]


def iter_gated_features_declarations():
    """Yield ``(model, gated_features)`` for every installed model declaring ``gated_features``."""
    for model in apps.get_models():
        if hasattr(model, "gated_features"):
            yield model, model.gated_features


def iter_declared_gated_features():
    """Yield ``(model, perm)`` for every ``gated_features`` entry declared on an installed model.

    A declaration that is not a list (a lone string for instance) is ignored: the system check reports it.
    """
    for model, declaration in iter_gated_features_declarations():
        if not isinstance(declaration, str):
            for perm in declaration:
                yield model, perm


def get_declared_permissions():
    """Return the ``"app_label.codename"`` of every permission declared by an installed model."""
    permissions = set()
    for model in apps.get_models():
        opts = model._meta
        permissions.update(
            f"{opts.app_label}.{get_permission_codename(action, opts)}" for action in opts.default_permissions
        )
        permissions.update(f"{opts.app_label}.{codename}" for codename, _name in opts.permissions)
    return permissions


@cache
def get_gated_features():
    """Return the ``(codename, perm)`` pairs of all the gated features, without duplicates.

    The codename (part after the ``"."``) is the key exposed to the front-end, so that it can reference
    ``permissions.set_on_start`` without knowing about app labels.

    The result is cached: call ``get_gated_features.cache_clear()`` if the installed models change
    (e.g. in tests).
    """
    return tuple(dict.fromkeys((perm_codename(perm), str(perm)) for _model, perm in iter_declared_gated_features()))


def get_user_gated_features(user):
    """Return ``{codename: bool}`` telling which gated features ``user`` is allowed to use."""
    return {codename: user.has_perm(perm) for codename, perm in get_gated_features()}
