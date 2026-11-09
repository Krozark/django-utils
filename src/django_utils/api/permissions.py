from rest_framework.permissions import SAFE_METHODS, BasePermission, DjangoModelPermissions, IsAuthenticated

__all__ = [
    "FullModelPermissions",
    "AllowNone",
    "IsSuperuser",
    "CurrentUser",
    "CurrentUserOrSuperuser",
    "CurrentUserOrSuperuserOrReadOnly",
    "CreatedByObjectPermission",
]


class FullModelPermissions(DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class AllowNone(BasePermission):
    def has_permission(self, request, view):
        return False


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class CurrentUser(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.pk == user.pk


class CurrentUserOrSuperuser(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.is_superuser or obj.pk == user.pk


class CurrentUserOrSuperuserOrReadOnly(CurrentUserOrSuperuser):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) or request.method in SAFE_METHODS


class CreatedByObjectPermission(BasePermission):
    """Permission that checks if object.created_by == request.user.

    For objects without created_by field, permission is granted.
    """

    def has_object_permission(self, request, view, obj):
        # If object doesn't have created_by, allow access
        if not hasattr(obj, "created_by"):
            return True

        # Check if user owns the object
        return obj.created_by == request.user
