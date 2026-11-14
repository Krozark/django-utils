import tempfile
from pathlib import Path
from shutil import rmtree

from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages

try:
    from freezegun import freeze_time
except ImportError:  # pragma: no cover - depends on the installed extras
    freeze_time = None

__all__ = ["FrozenTimeMixin", "MediaCleanupMixin"]


class FrozenTimeMixin:
    """Freeze the clock for the whole test class when ``frozen_time`` is set (needs the ``testing`` extra)."""

    frozen_time = None

    @classmethod
    def setUpClass(cls):
        if cls.frozen_time is not None:
            if freeze_time is None:
                raise ImproperlyConfigured("frozen_time requires freezegun: install django-utils[testing].")
            freezer = freeze_time(cls.frozen_time)
            freezer.start()
            cls.addClassCleanup(freezer.stop)
        super().setUpClass()


class MediaCleanupMixin:
    """Empty the filesystem storages listed in ``storages_to_clear`` before/after the class and after each test.

    Only directories inside the system temporary directory are removed, so a misconfigured test
    environment can never wipe real media files.
    """

    storages_to_clear = ("default",)

    @classmethod
    def setUpClass(cls):
        cls.clear_media_storages()
        cls.addClassCleanup(cls.clear_media_storages)
        super().setUpClass()

    def tearDown(self):
        super().tearDown()
        self.clear_media_storages()

    @classmethod
    def clear_media_storages(cls):
        for alias in cls.storages_to_clear:
            storage = storages[alias]
            if not isinstance(storage, FileSystemStorage):
                continue
            location = storage.location
            if not Path(location).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
                raise ImproperlyConfigured(
                    f"Refusing to clear storage '{alias}': {location} is not inside the temporary directory. "
                    "Point the storage to a temporary location in your test settings."
                )
            rmtree(location, ignore_errors=True)
