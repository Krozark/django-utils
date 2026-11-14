from django.test import TestCase, override_settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from django_utils.api.pagination import StandardResultsSetPagination
from django_utils.api.renderers import HTMXRenderer, StandardJSONRenderer
from django_utils.testing.api import ViewSetContractTestCase
from tests.testing.api.viewsets import ContractItemFilterSet, ContractItemSerializer, ContractItemViewSet
from tests.testing.factories import ContractItemFactory, UserFactory
from tests.testing.helpers import failed_test_names, run_contract


@override_settings(ROOT_URLCONF="tests.testing.api.urls")
class ContractItemViewSetContract(ViewSetContractTestCase):
    viewset_class = ContractItemViewSet
    url_basename = "contractitem"
    action_url_kwargs = {"retrieve": {"slug": "first"}}
    users = {
        "anonymous": None,
        "user": lambda: UserFactory(username="user"),
        "admin": lambda: UserFactory(username="admin", is_staff=True),
    }

    expected_lookup_field = "slug"
    expected_actions = ["list", "retrieve", "titles"]
    expected_filter_backends = [DjangoFilterBackend]
    expected_filterset_classes = {
        "list": ContractItemFilterSet,
        "retrieve": ContractItemFilterSet,
        "titles": ContractItemFilterSet,
    }
    expected_serializer_classes = {"list": ContractItemSerializer, "retrieve": ContractItemSerializer}
    expected_pagination_class = StandardResultsSetPagination
    expected_renderer_classes = [StandardJSONRenderer, HTMXRenderer]
    expected_parser_classes = [JSONParser, FormParser, MultiPartParser]
    expected_permissions = [
        {"action": action, "user": user, "allowed": user != "anonymous"}
        for action in ("list", "retrieve", "titles")
        for user in ("anonymous", "user", "admin")
    ]
    expected_querysets = [
        {"user": "anonymous", "instances": [0, 1]},
        {"user": "user", "instances": [0, 1]},
        {"user": "admin", "instances": [0, 1, 2]},
        {"user": "admin", "action": "titles", "query_params": {"is_active": "true"}, "instances": [0, 1, 2]},
    ]
    expected_orderings = [{"user": "admin", "instances": [0, 1, 2]}]
    expected_query_counts = [
        {"action": "list", "user": "admin", "count": 2},
        {"action": "list", "user": "admin", "query_params": {"is_active": "true"}, "count": 2},
        {"action": "retrieve", "user": "user", "count": 1},
        {"action": "titles", "user": "admin", "count": 1},
    ]

    def create_fixtures(self):
        self.instances = [
            ContractItemFactory(pk=1, slug="first", title="Alpha"),
            ContractItemFactory(pk=2, slug="second", title="Bravo"),
            ContractItemFactory(pk=3, slug="hidden", title="Charlie", is_active=False),
        ]


class ViewSetContractViolationTests(TestCase):
    def failures(self, **overrides):
        case = type("Variation", (ContractItemViewSetContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_lookup_field(self):
        self.assertEqual(self.failures(expected_lookup_field="pk"), {"test_lookup_field"})

    def test_missing_action(self):
        self.assertEqual(
            self.failures(expected_actions=["list", "retrieve", "titles", "create"]),
            {"test_expected_actions", "test_permissions_coverage", "test_filterset_classes_coverage"},
        )

    def test_undeclared_action(self):
        self.assertEqual(self.failures(expected_actions=["list", "retrieve"]), {"test_unexpected_actions"})

    def test_filter_backends(self):
        self.assertEqual(self.failures(expected_filter_backends=[]), {"test_unexpected_filter_backends"})
        self.assertEqual(
            self.failures(expected_filter_backends=[DjangoFilterBackend, dict]), {"test_expected_filter_backends"}
        )

    def test_filterset_class(self):
        classes = {**ContractItemViewSetContract.expected_filterset_classes, "list": None}
        self.assertEqual(self.failures(expected_filterset_classes=classes), {"test_expected_filterset_classes"})

    def test_serializer_class(self):
        self.assertEqual(
            self.failures(expected_serializer_classes={"list": dict}), {"test_expected_serializer_classes"}
        )

    def test_pagination_class(self):
        self.assertEqual(self.failures(expected_pagination_class=None), {"test_expected_pagination_class"})

    def test_renderer_and_parser_classes(self):
        self.assertEqual(
            self.failures(expected_renderer_classes=[StandardJSONRenderer]), {"test_expected_renderer_classes"}
        )
        self.assertEqual(self.failures(expected_parser_classes=[JSONParser]), {"test_expected_parser_classes"})

    def test_wrong_permission(self):
        permissions = [
            {**case, "allowed": not case["allowed"]} if (case["action"], case["user"]) == ("list", "user") else case
            for case in ContractItemViewSetContract.expected_permissions
        ]
        self.assertEqual(self.failures(expected_permissions=permissions), {"test_expected_permissions"})

    def test_missing_permission_case_fails_in_strict_mode(self):
        permissions = ContractItemViewSetContract.expected_permissions[1:]
        self.assertEqual(self.failures(expected_permissions=permissions), {"test_permissions_coverage"})
        self.assertEqual(self.failures(expected_permissions=permissions, strict_coverage=False), set())

    def test_wrong_queryset(self):
        querysets = [{"user": "anonymous", "instances": [0, 1, 2]}, *ContractItemViewSetContract.expected_querysets[1:]]
        self.assertEqual(self.failures(expected_querysets=querysets), {"test_expected_querysets"})

    def test_missing_queryset_user_fails_in_strict_mode(self):
        querysets = ContractItemViewSetContract.expected_querysets[1:]
        self.assertEqual(self.failures(expected_querysets=querysets), {"test_querysets_coverage"})

    def test_wrong_ordering(self):
        self.assertEqual(
            self.failures(expected_orderings=[{"user": "admin", "instances": [2, 1, 0]}]), {"test_expected_orderings"}
        )

    def test_wrong_query_count(self):
        counts = [
            {"action": "list", "user": "admin", "count": 5},
            *ContractItemViewSetContract.expected_query_counts[1:],
        ]
        self.assertEqual(self.failures(expected_query_counts=counts), {"test_expected_query_counts"})

    def test_missing_query_count_fails_in_strict_mode(self):
        counts = ContractItemViewSetContract.expected_query_counts[:-1]
        self.assertEqual(self.failures(expected_query_counts=counts), {"test_query_counts_coverage"})

    def test_missing_filterset_case_fails_in_strict_mode(self):
        classes = {"list": ContractItemFilterSet}
        self.assertEqual(self.failures(expected_filterset_classes=classes), {"test_filterset_classes_coverage"})
