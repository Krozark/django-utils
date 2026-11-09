import importlib
from importlib.metadata import PackageNotFoundError
from unittest import mock

from django.apps import apps
from django.test import SimpleTestCase

import django_utils


class DjangoUtilsAppTests(SimpleTestCase):
    def test_app_is_installed(self):
        self.assertEqual(apps.get_app_config("django_utils").name, "django_utils")

    def test_version_is_exposed(self):
        self.assertTrue(django_utils.__version__)


class VersionFallbackTests(SimpleTestCase):
    def test_version_without_installed_metadata(self):
        with mock.patch("importlib.metadata.version", side_effect=PackageNotFoundError):
            reloaded = importlib.reload(django_utils)
            self.assertEqual(reloaded.__version__, "0+unknown")
        importlib.reload(django_utils)
