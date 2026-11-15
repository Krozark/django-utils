import re
from collections import Counter

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status

from ..transactions import database_aliases_of, rollback_atomic

__all__ = ["QueryCountMixin"]

# Literals (and lists of literals) of a SQL query, replaced to compare queries regardless of their parameters.
_SQL_LITERALS = re.compile(r"""(?:'[^']*'|\b\d+\b)(?:, (?:'[^']*'|\b\d+\b))*""")


class QueryCountMixin:
    """Detect N+1 queries: a GET must run a fixed budget of SQL queries, whatever the amount of data.

    By default, a GET on an object runs ``DETAIL_QUERY_COUNT`` query, and a GET on a paginated list (a response
    holding ``results``) runs ``LIST_QUERY_COUNT`` queries. Override them in a test class to change the default, or
    declare the total of an endpoint that needs more (prefetches, permission checks...) as ``expected``, with a
    comment explaining why. The requests go through ``self.client``: authenticate it beforehand.
    """

    DETAIL_QUERY_COUNT = 1
    LIST_QUERY_COUNT = 2  # the COUNT of the pagination, and the objects

    def _get_queries(self, url):
        """Return the queries run by a GET, and the number of queries it is expected to run by default."""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        is_paginated = isinstance(response.data, dict) and "results" in response.data
        expected = self.LIST_QUERY_COUNT if is_paginated else self.DETAIL_QUERY_COUNT
        return Counter(_SQL_LITERALS.sub("?", query["sql"]) for query in context.captured_queries), expected

    def assert_query_count(self, url, create, expected=None):
        """Assert that GET ``url`` runs the same, expected, number of queries with 2 then 3 objects.

        ``create`` is called with no argument to add an object exposed by ``url``: a row for a list endpoint, a
        nested object for a detail endpoint. ``expected`` overrides the default budget.
        """
        create()
        self._get_queries(url)  # warm up process-wide caches (ContentType, permissions...)
        create()
        first, default = self._get_queries(url)
        create()
        second, _ = self._get_queries(url)
        expected = default if expected is None else expected
        repeated = "\n".join(f"{count} more: {sql}" for sql, count in (second - first).items())
        self.assertEqual(
            (first.total(), second.total()),
            (expected, expected),
            f"GET {url}: expected {expected} queries, got {first.total()} then {second.total()} with more data:\n"
            f"{repeated}\n" + "\n".join(first),
        )

    def assert_query_counts(self, cases):
        """Run ``assert_query_count`` as a sub-test for each ``{url: create}`` or ``{url: (create, expected)}`` item.

        The data added by a case is rolled back, so that it cannot fill the page of the next ones.
        """
        for url, case in cases.items():
            create, *expected = case if isinstance(case, tuple) else (case,)
            with self.subTest(url=url), rollback_atomic(database_aliases_of(self)):
                self.assert_query_count(url, create, *expected)
