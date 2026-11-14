import functools
import re
from collections.abc import Callable, Mapping

from .transactions import database_aliases_of, rollback_atomic

__all__ = ["subtests_cases", "with_fixtures"]

_CASE_KEYS = {"data", "raises", "message"}


def _normalize_case(name, case):
    if not isinstance(case, Mapping):
        return case, None, None

    unknown = set(case) - _CASE_KEYS
    if unknown:
        raise ValueError(f"Case '{name}' has unknown keys {sorted(unknown)}, allowed: {sorted(_CASE_KEYS)}")
    if "data" not in case:
        raise ValueError(f"Case '{name}' must define 'data'")
    return case["data"], case.get("raises"), case.get("message")


def subtests_cases(cases: Mapping[str, object]) -> Callable:
    """Run the decorated test once per case, each one in its own sub-test and rolled-back transaction.

    A case is either its data (list/tuple) or a dict ``{"data": ..., "raises": Exception, "message": "..."}``
    when the case is expected to raise.
    """
    normalized = {name: _normalize_case(name, case) for name, case in cases.items()}

    def decorator(test_method):
        @functools.wraps(test_method)
        def wrapper(self, *args):
            for name, (data, raises, message) in normalized.items():
                with self.subTest(case=name), rollback_atomic(database_aliases_of(self)):
                    if raises is None:
                        test_method(self, data, *args)
                    elif message is None:
                        with self.assertRaises(raises):
                            test_method(self, data, *args)
                    else:
                        with self.assertRaisesMessage(raises, message):
                            test_method(self, data, *args)

        return wrapper

    return decorator


def with_fixtures(fixtures_method_name: str | None = None) -> Callable:
    """Call ``fixtures_<name>()`` (or the given method) before ``test_<name>()`` to build its fixtures."""

    def decorator(test_method):
        @functools.wraps(test_method)
        def wrapper(self, *args):
            method_name = fixtures_method_name or re.sub(r"^test_", "fixtures_", test_method.__name__)
            try:
                fixtures_method = getattr(self, method_name)
            except AttributeError:
                raise AttributeError(f"Fixtures method {method_name} not found") from None
            fixtures_method()
            return test_method(self, *args)

        return wrapper

    return decorator
