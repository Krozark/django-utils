from django.contrib import admin
from django.utils.translation import gettext_lazy as _

__all__ = [
    "IsPublicAdminMixin",
    "CreatedByAdminMixin",
    "ReadOnlyAdminMixin",
]


class _CreatedByFilter(admin.SimpleListFilter):
    """Free-text filter on the username of ``created_by``."""

    template = "django_utils/admin/input_filter.html"
    title = _("user")

    def __init__(self, request, params, model, model_admin):
        user_model = model._meta.get_field("created_by").related_model
        self.parameter_name = f"created_by__{user_model.USERNAME_FIELD}"
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return ((),)

    def choices(self, changelist):
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v) for k, v in changelist.get_filters_params().items() if k != self.parameter_name
        )
        yield all_choice

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{f"{self.parameter_name}__icontains": self.value()})
        return queryset


class IsPublicAdminMixin(admin.ModelAdmin):
    """Admin for ``IsPublicMixin`` models: ``is_public`` is only editable by superusers.

    The admin lists every object, public or not: ``IsPublicMixin`` makes the unfiltered ``objects`` the
    default manager, which is the one ``ModelAdmin`` uses.
    """

    def get_list_display(self, request):
        return (*super().get_list_display(request), "is_public")

    def get_list_filter(self, request):
        return ("is_public", *super().get_list_filter(request))

    def get_exclude(self, request, obj=None):
        exclude = super().get_exclude(request, obj=obj) or ()
        if not request.user.is_superuser:
            return (*exclude, "is_public")
        return exclude


class CreatedByAdminMixin(admin.ModelAdmin):
    """Admin for ``CreatedByMixin`` models: users only see and edit their own objects (superusers see all)."""

    def get_list_display(self, request):
        return (*super().get_list_display(request), "created_by", "created_at")

    def get_list_filter(self, request):
        return (_CreatedByFilter, *super().get_list_filter(request))

    def get_exclude(self, request, obj=None):
        return (*(super().get_exclude(request, obj=obj) or ()), "id", "created_by")

    def get_readonly_fields(self, request, obj=None):
        if not self.has_change_permission(request, obj):
            exclude = self.get_exclude(request, obj=obj)
            return [field.name for field in self.model._meta.fields if field.editable and field.name not in exclude]
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        # Only stamp created_by on creation: touching it on edit would silently transfer
        # the ownership of an existing object.
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.created_by != request.user:
            return request.user.is_superuser
        return super().has_delete_permission(request, obj=obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.created_by != request.user:
            return request.user.is_superuser
        return super().has_change_permission(request, obj=obj)


class ReadOnlyAdminMixin(admin.ModelAdmin):
    """Admin that displays every field as read-only and forbids adding or changing objects."""

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
