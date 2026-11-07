from django.apps import apps
from django.test import SimpleTestCase

import django_utils


class DjangoUtilsAppTests(SimpleTestCase):
    def test_app_is_installed(self):
        self.assertEqual(apps.get_app_config("django_utils").name, "django_utils")

    def test_version_is_exposed(self):
        self.assertTrue(django_utils.__version__)
