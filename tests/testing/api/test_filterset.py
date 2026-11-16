import django_filters
from django.test import TestCase

from django_utils.testing.api import FilterSetContractTestCase
from tests.testing.api.viewsets import ContractItemFilterSet
from tests.testing.factories import ContractItemFactory, UserFactory
from tests.testing.helpers import failed_test_names, run_contract


class ContractItemFilterSetContract(FilterSetContractTestCase):
    filterset_class = ContractItemFilterSet
    users = {"admin": lambda: UserFactory(is_staff=True)}

    expected_filters = {
        "is_active": django_filters.BooleanFilter,
        "title": (django_filters.CharFilter, django_filters.Filter),
        "min_id": django_filters.NumberFilter,
    }

    def setUp(self):
        self.instances = [
            ContractItemFactory(pk=1, title="Alpha", is_active=True),
            ContractItemFactory(pk=2, title="Bravo", is_active=False),
            ContractItemFactory(pk=3, title="alphabet", is_active=True),
        ]

    def test_filter_is_active(self):
        self.assert_filter("is_active", data={"is_active": "true"}, expected_instances=[0, 2])
        self.assert_filter("is_active", data={"is_active": "false"}, expected_instances=[1])

    def test_filter_title(self):
        self.assert_filter("title", data={"title": "alpha"}, user="admin", expected_instances=[0, 2])
        self.assert_filter("title", data={}, expected_instances=[0, 1, 2])

    def test_filter_min_id(self):
        self.assert_filter("min_id", data={"min_id": "2"}, expected_instances=[1, 2])
        self.assert_filter(
            "min_id", data={"min_id": "abc"}, expected_instances=[0, 1, 2], expected_errors=["Enter a number."]
        )

    def test_assert_filter_detects_wrong_instances(self):
        with self.assertRaises(self.failureException):
            self.assert_filter("is_active", data={"is_active": "true"}, expected_instances=[1])

    def test_assert_filter_detects_wrong_errors(self):
        with self.assertRaises(self.failureException):
            self.assert_filter("min_id", data={"min_id": "abc"}, expected_instances=[0, 1, 2])

    def test_explicit_queryset(self):
        queryset = self.instances[0].__class__.objects.filter(pk__in=[1, 2])
        self.assert_filter("is_active", data={"is_active": "true"}, queryset=queryset, expected_instances=[0])


class FilterSetContractViolationTests(TestCase):
    def failures(self, **overrides):
        case = type("Variation", (ContractItemFilterSetContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_filter_class(self):
        filters = {**ContractItemFilterSetContract.expected_filters, "title": django_filters.NumberFilter}
        self.assertEqual(self.failures(expected_filters=filters), {"test_expected_filters"})

    def test_undeclared_filter(self):
        filters = {k: v for k, v in ContractItemFilterSetContract.expected_filters.items() if k != "title"}
        self.assertEqual(self.failures(expected_filters=filters, test_filter_title=None), {"test_unexpected_filters"})

    def test_missing_filter_test(self):
        self.assertEqual(self.failures(test_filter_title=None), {"test_all_filters_are_tested"})
