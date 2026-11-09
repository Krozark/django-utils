import re

from django.core import checks

from .registry import (
    get_declared_permissions,
    iter_declared_gated_features,
    iter_gated_features_declarations,
    perm_codename,
)

__all__ = [
    "check_gated_features",
]

PERMISSION_RE = re.compile(r"^\w+\.\w+$")


@checks.register()
def check_gated_features(app_configs=None, **kwargs):
    """Make sure every ``gated_features`` entry is a permission that really exists, with a unique codename."""
    errors = []
    declared_permissions = get_declared_permissions()
    perms_by_codename = {}

    for model, declaration in iter_gated_features_declarations():
        if isinstance(declaration, str):
            errors.append(
                checks.Error(
                    f"{model._meta.label}.gated_features must be a list of permissions, not a string.",
                    obj=model,
                    id="django_utils.E001",
                )
            )

    for model, perm in iter_declared_gated_features():
        label = model._meta.label
        if not isinstance(perm, str) or not PERMISSION_RE.match(perm):
            errors.append(
                checks.Error(
                    f"{label}.gated_features: {perm!r} is not a permission of the form 'app_label.codename'.",
                    obj=model,
                    id="django_utils.E001",
                )
            )
        elif perm not in declared_permissions:
            errors.append(
                checks.Error(
                    f"{label}.gated_features: the permission {perm!r} is not declared by any installed model.",
                    hint="Declare it in the 'permissions' of a model Meta, or fix the typo.",
                    obj=model,
                    id="django_utils.E002",
                )
            )
        else:
            perms_by_codename.setdefault(perm_codename(perm), set()).add(perm)

    for codename, perms in perms_by_codename.items():
        if len(perms) > 1:
            errors.append(
                checks.Error(
                    f"The gated features {sorted(perms)} share the codename {codename!r}, they cannot be told apart.",
                    id="django_utils.E003",
                )
            )
    return errors
