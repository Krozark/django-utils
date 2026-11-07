"""Reusable Django utilities."""

from importlib.metadata import version

__all__ = ["__version__"]

__version__ = version("django-utils")
