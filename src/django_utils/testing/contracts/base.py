import unittest

from django.core.exceptions import ImproperlyConfigured

__all__ = ["ContractMixin"]

LIBRARY_PACKAGE = "django_utils.testing"


class ContractMixin:
    """Base of the contract test cases: declare ``required_attributes`` the concrete class must define.

    The library's own base classes are skipped when they get collected (e.g. because they were imported
    in a test module), while a project class forgetting one of them fails loudly.
    """

    required_attributes = ()

    @classmethod
    def setUpClass(cls):
        missing = [name for name in cls.required_attributes if getattr(cls, name, None) is None]
        if missing:
            if cls.__module__.startswith(LIBRARY_PACKAGE):
                raise unittest.SkipTest(f"{cls.__name__} is an abstract contract")
            raise ImproperlyConfigured(f"{cls.__name__} must define: {', '.join(missing)}")
        super().setUpClass()
