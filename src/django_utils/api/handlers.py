from rest_framework.views import exception_handler

from .envelope import error_envelope

__all__ = [
    "custom_exception_handler",
]


def custom_exception_handler(exc, context):
    """DRF exception handler that returns errors in the standard envelope."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data = error_envelope(response.data, response.status_code)
    return response
