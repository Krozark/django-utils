from contextlib import contextmanager
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS

from ..contracts.base import ContractMixin
from ..decorators import with_fixtures
from ..testcases import TestCase
from ..transactions import database_aliases_of, rollback_atomic
from .requests import RequestBuilderMixin

__all__ = ["ViewSetContractTestCase"]

# action name -> (HTTP method, route kind, is detail)
CRUD_ACTIONS = {
    "list": ("GET", "list", False),
    "create": ("POST", "list", False),
    "retrieve": ("GET", "detail", True),
    "update": ("PUT", "detail", True),
    "partial_update": ("PATCH", "detail", True),
    "destroy": ("DELETE", "detail", True),
}
DENIED_STATUSES = (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


class ViewSetContractTestCase(ContractMixin, RequestBuilderMixin, TestCase):
    """Contract of a DRF viewset, exercised through the real URLs (the test must set ``ROOT_URLCONF``).

    Setup:
    - ``viewset_class`` and ``url_basename`` (router basename, so routes are ``<basename>-list``, ``-detail``...).
    - ``action_url_kwargs``: ``{action: url kwargs}`` for detail routes; a value may be a callable taking the
      test case, to use objects created by ``create_fixtures``.
    - ``users``: ``{key: None | user | callable}``, ``None`` being the anonymous user.

    Class-level expectations: ``expected_lookup_field``, ``expected_actions``, ``expected_filter_backends``,
    ``expected_filterset_classes`` (``{action: class | None}``), ``expected_serializer_classes``
    (``{action: class}``), ``expected_pagination_class``, ``expected_renderer_classes``,
    ``expected_parser_classes``.

    Behavioural expectations, all lists of dicts where ``user`` is a ``users`` key, ``action`` defaults to
    ``"list"``, ``query_params`` to ``{}`` and ``instances`` are indexes in ``self.instances``:
    - ``expected_permissions``: ``{"action", "user", "allowed", "query_params", "data"}``.
    - ``expected_querysets``: ``{"user", "action", "query_params", "instances"}`` against ``get_queryset()``.
    - ``expected_orderings``: same keys, ordered, against the filtered queryset.
    - ``expected_query_counts``: ``{"action", "user", "query_params", "count"}``.

    With ``strict_coverage`` (default), the contract also fails when an action x user permission, an action
    filterset, a user queryset or a safe action query count is not declared.
    """

    required_attributes = ("viewset_class", "url_basename")

    viewset_class = None
    url_basename = None
    action_url_kwargs = {}
    users = {"anonymous": None}
    strict_coverage = True

    expected_lookup_field = None
    expected_actions = []
    expected_filter_backends = []
    expected_filterset_classes = {}
    expected_serializer_classes = {}
    expected_pagination_class = None
    expected_renderer_classes = []
    expected_parser_classes = []
    expected_permissions = []
    expected_querysets = []
    expected_orderings = []
    expected_query_counts = []

    # --- routing -----------------------------------------------------------------------------------------------

    @property
    def actions_mapping(self):
        """``{action: (HTTP method, view name, is detail)}`` for the CRUD and the extra actions of the viewset."""
        mapping = {
            name: (method, f"{self.url_basename}-{route}", detail)
            for name, (method, route, detail) in CRUD_ACTIONS.items()
            if callable(getattr(self.viewset_class, name, None))
        }
        for extra_action in self.viewset_class.get_extra_actions():
            method = next(iter(extra_action.mapping)).upper()
            mapping[extra_action.__name__] = (
                method,
                f"{self.url_basename}-{extra_action.url_name}",
                extra_action.detail,
            )
        return mapping

    def resolve_url_kwargs(self, action):
        url_kwargs = self.action_url_kwargs.get(action, {})
        return url_kwargs(self) if callable(url_kwargs) else url_kwargs

    def build_path(self, action, query_params=None):
        _, view_name, _ = self.actions_mapping[action]
        path = reverse(view_name, kwargs=self.resolve_url_kwargs(action))
        return f"{path}?{urlencode(query_params, doseq=True)}" if query_params else path

    @contextmanager
    def authenticated_as(self, user_key=None):
        """Make the test client act as ``users[user_key]`` (anonymous when ``None``) inside the block.

        Authenticating and resetting go through DRF's ``force_authenticate``, which may query the session
        table: use this around ``assertNumQueries`` rather than inside it.
        """
        self.client.force_authenticate(user=self.users[user_key] if user_key is not None else None)
        try:
            yield
        finally:
            self.client.force_authenticate(user=None)

    def send_request(self, action, query_params=None, data=None):
        """Call ``action`` through the test client with the current authentication."""
        method, _, _ = self.actions_mapping[action]
        request_kwargs = {"format": "json", "data": data} if data is not None else {}
        return getattr(self.client, method.lower())(self.build_path(action, query_params), **request_kwargs)

    def get_response(self, action, user_key=None, query_params=None, data=None):
        """Call ``action`` through the test client, authenticated as ``users[user_key]`` for that call only."""
        with self.authenticated_as(user_key):
            return self.send_request(action, query_params, data)

    def build_viewset(self, action, user_key=None, query_params=None):
        """A viewset instance ready for ``get_queryset()``/``get_serializer_class()``, as if serving ``action``."""
        method, _, detail = self.actions_mapping[action]
        user = self.users[user_key] if user_key is not None else None

        viewset = self.viewset_class()
        viewset.action = action
        viewset.detail = detail
        viewset.args = ()
        viewset.kwargs = self.resolve_url_kwargs(action)
        viewset.format_kwarg = None
        viewset.request = self.build_request(
            method=method, path=self.build_path(action), query_params=query_params, user=user
        )
        for extra_action in self.viewset_class.get_extra_actions():
            if extra_action.__name__ == action:
                for name, value in extra_action.kwargs.items():
                    setattr(viewset, name, value)
        return viewset

    # --- class configuration -----------------------------------------------------------------------------------

    def test_lookup_field(self):
        self.assertEqual(self.viewset_class.lookup_field, self.expected_lookup_field)

    def test_expected_actions(self):
        for action in self.expected_actions:
            with self.subTest(case=action):
                self.assertIn(action, self.actions_mapping)

    def test_unexpected_actions(self):
        for action in self.actions_mapping:
            with self.subTest(case=action):
                self.assertIn(action, self.expected_actions)

    def test_expected_filter_backends(self):
        for backend in self.expected_filter_backends:
            with self.subTest(case=backend):
                self.assertIn(backend, self.viewset_class.filter_backends)

    def test_unexpected_filter_backends(self):
        for backend in self.viewset_class.filter_backends:
            with self.subTest(case=backend):
                self.assertIn(backend, self.expected_filter_backends)

    def test_expected_filterset_classes(self):
        for action, expected in self.expected_filterset_classes.items():
            with self.subTest(case=action):
                viewset = self.build_viewset(action)
                get_filterset_class = getattr(viewset, "get_filterset_class", None)
                actual = (
                    get_filterset_class()
                    if callable(get_filterset_class)
                    else getattr(viewset, "filterset_class", None)
                )
                self.assertEqual(actual, expected)

    def test_filterset_classes_coverage(self):
        self._check_coverage(
            {(action,) for action in self.expected_actions},
            {(action,) for action in self.expected_filterset_classes},
            "expected_filterset_classes",
        )

    def test_expected_serializer_classes(self):
        for action, expected in self.expected_serializer_classes.items():
            with self.subTest(case=action):
                self.assertEqual(self.build_viewset(action).get_serializer_class(), expected)

    def test_expected_pagination_class(self):
        self.assertEqual(self.viewset_class.pagination_class, self.expected_pagination_class)

    def test_expected_renderer_classes(self):
        self.assertCountEqual(self.viewset_class.renderer_classes, self.expected_renderer_classes)

    def test_expected_parser_classes(self):
        self.assertCountEqual(self.viewset_class.parser_classes, self.expected_parser_classes)

    # --- behaviour ---------------------------------------------------------------------------------------------

    def fixtures_expected_querysets(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_querysets(self):
        for index, case in enumerate(self.expected_querysets):
            with self.subTest(case=self._case_label(case, index)):
                viewset = self._build_case_viewset(case)
                expected = [self.instances[i] for i in case["instances"]]
                self.assertQuerySetEqual(viewset.get_queryset(), expected, ordered=False)

    def test_querysets_coverage(self):
        self._check_coverage(
            {(user,) for user in self.users},
            {(case["user"],) for case in self.expected_querysets},
            "expected_querysets",
        )

    def fixtures_expected_orderings(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_orderings(self):
        for index, case in enumerate(self.expected_orderings):
            with self.subTest(case=self._case_label(case, index)):
                viewset = self._build_case_viewset(case)
                queryset = viewset.filter_queryset(viewset.get_queryset())
                expected = [self.instances[i] for i in case["instances"]]
                self.assertQuerySetEqual(queryset, expected, ordered=True)

    def fixtures_expected_permissions(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_permissions(self):
        for index, case in enumerate(self.expected_permissions):
            with self.subTest(case=self._case_label(case, index)), rollback_atomic(database_aliases_of(self)):
                response = self.get_response(
                    case["action"], case["user"], query_params=case.get("query_params"), data=case.get("data")
                )
                if case["allowed"]:
                    self.assertNotIn(response.status_code, DENIED_STATUSES)
                else:
                    self.assertIn(response.status_code, DENIED_STATUSES)

    def test_permissions_coverage(self):
        self._check_coverage(
            {(action, user) for action in self.expected_actions for user in self.users},
            {(case["action"], case["user"]) for case in self.expected_permissions},
            "expected_permissions",
        )

    def fixtures_expected_query_counts(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_query_counts(self):
        for index, case in enumerate(self.expected_query_counts):
            with self.subTest(case=self._case_label(case, index)), rollback_atomic(database_aliases_of(self)):
                with self.authenticated_as(case["user"]), self.assertNumQueries(case["count"]):
                    response = self.send_request(case["action"], query_params=case.get("query_params"))
                self.assertTrue(status.is_success(response.status_code) or status.is_redirect(response.status_code))

    def test_query_counts_coverage(self):
        safe_actions = {
            action
            for action in self.expected_actions
            if action in self.actions_mapping and self.actions_mapping[action][0] in SAFE_METHODS
        }
        self._check_coverage(
            {(action,) for action in safe_actions},
            {(case["action"],) for case in self.expected_query_counts},
            "expected_query_counts",
        )

    # --- helpers -----------------------------------------------------------------------------------------------

    def _build_case_viewset(self, case):
        return self.build_viewset(case.get("action", "list"), case["user"], case.get("query_params"))

    @staticmethod
    def _case_label(case, index):
        return case.get("name") or ", ".join(str(case[key]) for key in ("action", "user") if key in case) or index

    def _check_coverage(self, required, declared, attribute_name):
        if not self.strict_coverage:
            self.skipTest("strict_coverage is disabled")
        missing = sorted(required - declared, key=str)
        self.assertFalse(missing, f"{type(self).__name__}.{attribute_name} misses cases for: {missing}")
