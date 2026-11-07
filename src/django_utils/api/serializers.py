from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from django_utils.models import CreatedByMixin, UUIDMixin

__all__ = [
    "RequestUserSerializerMixin",
    "GatedFieldsSerializerMixin",
    "UUIDMixinSerializer",
    "CreatedByMixinSerializer",
    "CreatedByAndUUIDMixinSerializer",
]


class RequestUserSerializerMixin:
    """Helpers to get (and check the permissions of) the user of the request in the serializer context."""

    def check_user(self):
        """Return the authenticated user of the request, or raise a ``ValidationError``."""
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            raise serializers.ValidationError(_("Request context is required."))

        user = request.user
        if not user.is_authenticated:
            raise serializers.ValidationError(_("Authentication required."))
        return user

    def check_perm(self, perm):
        """Return the authenticated user of the request if they have ``perm``, or raise a ``ValidationError``."""
        user = self.check_user()
        if not user.has_perm(perm):
            raise serializers.ValidationError(_("You do not have permission."))
        return user


class GatedFieldsSerializerMixin(RequestUserSerializerMixin):
    """Reserve some fields to the users having a permission.

    ``gated_fields`` maps field names to permissions. Writing a non-empty value in such a field without the
    permission is a validation error on this field; empty values are ignored, as they are a no-op.
    Must come before the serializer base class::

        class AmbienceSerializer(GatedFieldsSerializerMixin, serializers.ModelSerializer):
            gated_fields = {"on_start": "my_app.set_on_start"}
    """

    gated_fields = {}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        denied = {
            field: _("You do not have permission to edit this field.")
            for field, perm in self.gated_fields.items()
            if attrs.get(field) and not self.check_user().has_perm(perm)
        }
        if denied:
            raise serializers.ValidationError(denied)
        return attrs


class UUIDMixinSerializer(serializers.ModelSerializer):
    """Serializer for UUIDMixin: exposes the ``uuid`` as a read-only ``id``."""

    id = serializers.UUIDField(read_only=True, source="uuid")

    class Meta:
        model = UUIDMixin
        abstract = True
        fields = [
            "id",
        ]


class CreatedByMixinSerializer(RequestUserSerializerMixin, serializers.ModelSerializer):
    """Serializer for CreatedByMixin: read-only ownership and dates, ``created_by`` set from the request."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True, source="created_by.username")
    created_at_display = serializers.SerializerMethodField(help_text="Human-readable creation date")

    class Meta:
        model = CreatedByMixin
        abstract = True
        fields = [
            "created_by",
            "created_at",
            "updated_at",
            "created_at_display",
        ]
        read_only_fields = [
            "created_at_display",
        ]

    def create(self, validated_data):
        """Create with created_by set automatically."""
        validated_data["created_by"] = self.check_user()
        return super().create(validated_data)

    def get_created_at_display(self, obj):
        return obj.get_created_at_display()


class CreatedByAndUUIDMixinSerializer(CreatedByMixinSerializer, UUIDMixinSerializer):
    class Meta:
        abstract = True

        fields = UUIDMixinSerializer.Meta.fields + CreatedByMixinSerializer.Meta.fields
        read_only_fields = CreatedByMixinSerializer.Meta.fields
