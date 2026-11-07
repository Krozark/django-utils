from django_filters.rest_framework import BaseInFilter, UUIDFilter

__all__ = [
    "UUIDInFilter",
]


class UUIDInFilter(BaseInFilter, UUIDFilter):
    """Filter that accepts comma-separated UUIDs."""
