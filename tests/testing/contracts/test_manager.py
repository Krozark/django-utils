from django.test import TestCase

from django_utils.testing import ManagerContractTestCase
from tests.models import ContractItem, ContractItemManager
from tests.testing.factories import ContractItemFactory
from tests.testing.helpers import failed_test_names, run_contract


class ContractItemManagerContract(ManagerContractTestCase):
    model = ContractItem
    expected_manager_class = ContractItemManager
    expected_natural_keys = [
        {"key": ("does-not-exist",), "instance": None},
        {"key": ("first",), "instance": 0},
        {"key": ("second",), "instance": 1},
    ]
    expected_method_availabilities = {
        "active": {"manager": True, "queryset": True},
        "get_by_natural_key": {"manager": True, "queryset": False},
        "missing": {"manager": False, "queryset": False},
    }

    def fixtures_expected_natural_keys(self):
        self.instances = [ContractItemFactory(slug="first"), ContractItemFactory(slug="second")]


class ManagerContractViolationTests(TestCase):
    def failures(self, **overrides):
        case = type("Variation", (ContractItemManagerContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_manager_class(self):
        self.assertEqual(self.failures(expected_manager_class=dict), {"test_manager_class"})

    def test_wrong_natural_key_instance(self):
        keys = [{"key": ("first",), "instance": 1}]
        self.assertEqual(self.failures(expected_natural_keys=keys), {"test_expected_natural_keys"})

    def test_natural_key_not_expected_but_available(self):
        self.assertEqual(self.failures(expected_natural_keys=None), {"test_natural_key_availability"})

    def test_wrong_availability(self):
        availabilities = {"active": {"manager": True, "queryset": False}}
        self.assertEqual(self.failures(expected_method_availabilities=availabilities), {"test_method_availabilities"})

    def test_incomplete_availability_spec(self):
        availabilities = {"active": {"manager": True}}
        self.assertEqual(self.failures(expected_method_availabilities=availabilities), {"test_method_availabilities"})
