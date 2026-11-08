"""Reusable Django utilities."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("django-utils")
except PackageNotFoundError:  # running from a source tree that was not installed
    __version__ = "0+unknown"
