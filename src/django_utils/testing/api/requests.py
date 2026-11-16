from urllib.parse import urlencode

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

__all__ = ["RequestBuilderMixin"]


class RequestBuilderMixin:
    """Build WSGI/DRF requests, optionally authenticated as a given user, without going through the URL layer."""

    request_factory = APIRequestFactory()

    def build_wsgi_request(self, method="GET", path="/", query_params=None, user=None):
        url = f"{path}?{urlencode(query_params, doseq=True)}" if query_params else path
        wsgi_request = getattr(self.request_factory, method.lower())(url)
        if user is not None:
            force_authenticate(wsgi_request, user=user)
        return wsgi_request

    def build_request(self, *args, **kwargs):
        return Request(self.build_wsgi_request(*args, **kwargs))
