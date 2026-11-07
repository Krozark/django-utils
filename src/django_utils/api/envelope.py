"""The standard response envelope: ``{success, status_code, data, message, errors}``.

Shared by ``StandardJSONRenderer`` (wraps every response) and ``custom_exception_handler`` (wraps DRF exceptions).
"""

from django.utils.translation import gettext_lazy as _

__all__ = [
    "ENVELOPE_KEYS",
    "error_envelope",
    "format_errors",
    "get_error_message",
    "get_success_message",
    "is_envelope",
    "success_envelope",
]

ENVELOPE_KEYS = frozenset({"success", "status_code", "data", "message", "errors"})


def is_envelope(data):
    """Return True if ``data`` is already wrapped in the standard envelope."""
    return isinstance(data, dict) and ENVELOPE_KEYS.issubset(data)


def get_success_message(data, status_code):
    """Generate an appropriate success message."""
    if isinstance(data, dict) and "results" in data and "pagination" in data:
        return _("Data retrieved successfully")
    if status_code == 201:
        return _("Resource created successfully")
    if status_code == 204:
        return _("Resource deleted successfully")
    return _("Request successful")


def get_error_message(error_data):
    """Extract a readable error message from DRF error data."""
    if isinstance(error_data, dict):
        if "detail" in error_data:
            return error_data["detail"]
        if "non_field_errors" in error_data:
            return error_data["non_field_errors"][0] if error_data["non_field_errors"] else _("Validation error")
        if not error_data:
            return _("An error occurred")
        error_key, error = next(iter(error_data.items()))
        if isinstance(error, list):
            error = error[0]
        if error_key == "error":
            return error
        return f"{error_key}: {error}"
    if isinstance(error_data, list) and error_data:
        return error_data[0]
    return _("An error occurred")


def format_errors(error_data):
    """Flatten DRF error data into a ``dict[str, str]``, joining all the messages of a field.

    ``{'password': ['Error 1', 'Error 2']}`` becomes ``{'password': 'Error 1 Error 2'}``.
    Errors that are not bound to a field (``detail``, ``non_field_errors``, plain lists or strings)
    are stored under the ``error`` key. Returns ``None`` when there is no error data.
    """
    if error_data is None:
        return None

    if isinstance(error_data, dict):
        formatted_errors = {}
        for field, errors in error_data.items():
            if isinstance(errors, list):
                message = " ".join(str(e) for e in errors) if errors else _("Invalid value")
            else:
                message = errors
            key = "error" if field in ("detail", "non_field_errors") else field
            formatted_errors[key] = str(message)
        return formatted_errors

    if isinstance(error_data, list):
        return {"error": " ".join(str(e) for e in error_data) if error_data else str(_("An error occurred"))}

    return {"error": str(error_data)}


def success_envelope(data, status_code):
    return {
        "success": True,
        "status_code": status_code,
        "data": data,
        "message": get_success_message(data, status_code),
        "errors": None,
    }


def error_envelope(error_data, status_code):
    errors = format_errors(error_data)
    return {
        "success": False,
        "status_code": status_code,
        "data": None,
        "message": get_error_message(errors),
        "errors": errors,
    }
