import tempfile
from pathlib import Path
from shutil import rmtree

from django.apps import apps
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, storages

try:
    from freezegun import freeze_time
except ImportError:  # pragma: no cover - depends on the installed extras
    freeze_time = None

__all__ = ["CacheIsolationMixin", "FrozenTimeMixin", "MediaCleanupMixin", "clear_process_caches"]

PROCESS_CACHE_BACKENDS = (
    "django.core.cache.backends.locmem.LocMemCache",
    "django.core.cache.backends.dummy.DummyCache",
)


def clear_process_caches():
    """Empty the caches kept in the process, which a rolled back transaction does not undo.

    The content types and the local-memory caches. A shared cache (Redis, Memcached...) is never emptied.
    """
    if apps.is_installed("django.contrib.contenttypes"):
        apps.get_model("contenttypes", "ContentType").objects.clear_cache()
    for alias, options in settings.CACHES.items():
        if options["BACKEND"] in PROCESS_CACHE_BACKENDS:
            caches[alias].clear()


class CacheIsolationMixin:
    """Start each test without any cache of the process (content types, local-memory caches).

    A test cannot depend on what the previous one cached, nor on the order they run in: a query count, for instance,
    includes the queries a cache would otherwise save.
    """

    clear_caches = staticmethod(clear_process_caches)

    def _pre_setup(self):
        self.clear_caches()
        super()._pre_setup()


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
