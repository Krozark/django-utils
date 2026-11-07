from unittest import mock

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps

from django_utils.gating import checks, registry


class GatedFeaturesChecksTests(SimpleTestCase):
    def test_the_installed_models_are_valid(self):
        self.assertEqual(checks.check_gated_features(), [])

    def check(self, isolated_apps):
        with mock.patch.object(registry, "apps", isolated_apps):
            return [error.id for error in checks.check_gated_features()]

    @isolate_apps("tests", kwarg_name="isolated_apps")
    def test_valid_declarations(self, isolated_apps):
        class Valid(models.Model):
            gated_features = ["tests.use_it", "tests.add_valid"]

            class Meta:
                app_label = "tests"
                permissions = [("use_it", "Can use it")]

        self.assertEqual(self.check(isolated_apps), [])

    @isolate_apps("tests", kwarg_name="isolated_apps")
    def test_malformed_permission(self, isolated_apps):
        class Malformed(models.Model):
            gated_features = ["use_it", 42]

            class Meta:
                app_label = "tests"

        self.assertEqual(self.check(isolated_apps), ["django_utils.E001", "django_utils.E001"])

    @isolate_apps("tests", kwarg_name="isolated_apps")
    def test_unknown_permission(self, isolated_apps):
        class Unknown(models.Model):
            gated_features = ["tests.use_it"]

            class Meta:
                app_label = "tests"

        self.assertEqual(self.check(isolated_apps), ["django_utils.E002"])

    @isolate_apps("tests", "django.contrib.auth", kwarg_name="isolated_apps")
    def test_codename_shared_by_two_permissions(self, isolated_apps):
        class First(models.Model):
            gated_features = ["tests.use_it"]

            class Meta:
                app_label = "tests"
                permissions = [("use_it", "Can use it")]

        class Second(models.Model):
            gated_features = ["auth.use_it"]

            class Meta:
                app_label = "auth"
                permissions = [("use_it", "Can use it")]

        self.assertEqual(self.check(isolated_apps), ["django_utils.E003"])
