from django.test import SimpleTestCase as DjangoSimpleTestCase
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient

from .mixins import FrozenTimeMixin, MediaCleanupMixin

__all__ = ["SimpleTestCase", "TestCase"]


class SimpleTestCase(FrozenTimeMixin, DjangoSimpleTestCase):
    """Database-free test case with frozen-time support."""

    maxDiff = None


class TestCase(FrozenTimeMixin, MediaCleanupMixin, DjangoTestCase):
    """Django ``TestCase`` with frozen time, media cleanup, a DRF client and lazily built ``users``.

    ``users`` maps a key to ``None`` (anonymous), a model instance, or a callable creating the user
    (typically a factory-boy call). Callables are resolved once per class, in ``setUpTestData``.
    """

    maxDiff = None
    client_class = APIClient
    users = {}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.users = {key: user() if callable(user) else user for key, user in cls.users.items()}

    def get_user(self, key):
        return self.users[key]
