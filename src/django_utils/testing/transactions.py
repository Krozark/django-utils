from collections.abc import Iterable, Iterator
from contextlib import ExitStack, contextmanager

from django.db import DEFAULT_DB_ALIAS, connections, transaction

__all__ = ["rollback_atomic", "database_aliases_of"]


def database_aliases_of(test_case) -> list[str]:
    """Database aliases a test case is allowed to use (``databases`` attribute)."""
    databases = getattr(test_case, "databases", {DEFAULT_DB_ALIAS})
    if databases == "__all__":
        return list(connections)
    return sorted(databases)


@contextmanager
def rollback_atomic(using: Iterable[str] = (DEFAULT_DB_ALIAS,)) -> Iterator[None]:
    """Run the block inside ``atomic`` on each alias and always roll it back, even on success."""
    with ExitStack() as stack:
        for alias in using:
            stack.enter_context(_rolled_back(alias))
        yield


@contextmanager
def _rolled_back(alias: str) -> Iterator[None]:
    with transaction.atomic(using=alias):
        try:
            yield
        finally:
            transaction.set_rollback(True, using=alias)
