import re

from django import forms
from django.utils.translation import gettext_lazy as _

__all__ = [
    "FileSizeField",
]


class FileSizeField(forms.CharField):
    """Form field that accepts human-readable file sizes (e.g., '100MB', '1 GB') and cleans them to bytes."""

    SIZE_UNITS = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }
    SIZE_RE = re.compile(rf"^(\d+(?:\.\d+)?)({'|'.join(SIZE_UNITS)})?$")

    default_error_messages = {
        "invalid": _("Invalid format. Use: 100MB, 1GB, 500KB, etc."),
    }

    def prepare_value(self, value):
        """Convert bytes to human-readable format for display (locale-independent)."""
        if value is None or value == "" or value == 0:
            return 0
        try:
            size = int(value)
        except (ValueError, TypeError):
            return value
        for unit in ("TB", "GB", "MB", "KB"):
            unit_bytes = self.SIZE_UNITS[unit]
            if size >= unit_bytes:
                amount = size / unit_bytes
                if amount == int(amount):
                    return f"{int(amount)}{unit}"
                return f"{amount:.1f}{unit}"
        return f"{size}B"

    def clean(self, value):
        """Parse human-readable size to bytes."""
        value = super().clean(value)
        if not value:
            return 0

        match = self.SIZE_RE.match(value.upper().replace(" ", "").replace(",", "."))
        if not match:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")

        number, unit = match.groups()
        return int(float(number) * self.SIZE_UNITS[unit or "B"])
