import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages
from django.test import SimpleTestCase

from django_utils.testing import mixins
from django_utils.testing.mixins import FrozenTimeMixin, MediaCleanupMixin


@contextmanager
def override_storages(storages_settings):
    """Use ``storages_settings`` as the storages configuration.

    ``override_settings(STORAGES=...)`` is not enough before Django 5.1: the cache of ``storages`` is not
    reset and the ``OPTIONS`` of the backends are lost.
    """

    def configure(backends):
        storages.__dict__.pop("backends", None)
        storages._backends = backends
        storages._storages = {}

    configure(storages_settings)
    try:
        yield
    finally:
        configure(None)


def run_class_lifecycle(case_class):
    case_class.setUpClass()
    try:
        yield
    finally:
        case_class.tearDownClass()
        case_class.doClassCleanups()


class FrozenTimeMixinTests(SimpleTestCase):
    def test_time_is_frozen_during_the_class_only(self):
        class Frozen(FrozenTimeMixin, SimpleTestCase):
            frozen_time = "2012-01-14 03:21:34"

        for _ in run_class_lifecycle(Frozen):
            self.assertEqual(datetime.now(), datetime(2012, 1, 14, 3, 21, 34))
        self.assertGreater(datetime.now().year, 2020)

    def test_no_frozen_time_leaves_clock_alone(self):
        class NotFrozen(FrozenTimeMixin, SimpleTestCase):
            pass

        for _ in run_class_lifecycle(NotFrozen):
            self.assertGreater(datetime.now().year, 2020)

    def test_missing_freezegun_raises_explicit_error(self):
        class Frozen(FrozenTimeMixin, SimpleTestCase):
            frozen_time = "2012-01-14"

        with mock.patch.object(mixins, "freeze_time", None), self.assertRaisesMessage(ImproperlyConfigured, "testing"):
            Frozen.setUpClass()


class MediaCleanupMixinTests(SimpleTestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="django-utils-media-")
        self.addCleanup(lambda: Path(self.root).exists() and Path(self.root).rmdir())

    def storages_settings(self, location):
        return {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": location}},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }

    def test_directory_is_cleared_before_and_after_class_and_each_test(self):
        class Media(MediaCleanupMixin, SimpleTestCase):
            def test_nothing(self):
                pass

        with override_storages(self.storages_settings(self.root)):
            (Path(self.root) / "stale.txt").write_text("stale")
            Media.setUpClass()
            self.assertFalse(Path(self.root).exists())

            Path(self.root).mkdir()
            (Path(self.root) / "new.txt").write_text("new")
            test = Media("test_nothing")
            test.run()
            self.assertFalse(Path(self.root).exists())

            Path(self.root).mkdir()
            Media.doClassCleanups()
            self.assertFalse(Path(self.root).exists())
            Path(self.root).mkdir()

    def test_storage_without_location_is_ignored(self):
        class Media(MediaCleanupMixin, SimpleTestCase):
            storages_to_clear = ("default",)

        with override_storages(
            {"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}},
        ):
            self.assertNotIsInstance(storages["default"], FileSystemStorage)
            Media.setUpClass()
            Media.doClassCleanups()

    def test_refuses_to_clear_outside_temporary_directory(self):
        class Media(MediaCleanupMixin, SimpleTestCase):
            pass

        with (
            override_storages(self.storages_settings("/var/lib/not-temporary")),
            self.assertRaisesMessage(ImproperlyConfigured, "temporary"),
        ):
            Media.setUpClass()

    def test_clears_custom_storage_aliases(self):
        class Media(MediaCleanupMixin, SimpleTestCase):
            storages_to_clear = ("other",)

        other = tempfile.mkdtemp(prefix="django-utils-other-")
        settings = self.storages_settings(self.root)
        settings["other"] = {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": other}}
        with override_storages(settings):
            Media.setUpClass()
            self.assertFalse(Path(other).exists())
            self.assertTrue(Path(self.root).exists())
            Media.doClassCleanups()
