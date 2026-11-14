from django.db import models
from django.test import TestCase

from django_utils.testing import ModelContractTestCase
from tests.models import ContractItem
from tests.testing.factories import ContractItemFactory
from tests.testing.helpers import failed_test_names, run_contract


class ContractItemContract(ModelContractTestCase):
    model = ContractItem
    factory = ContractItemFactory
    build_kwargs = {"slug": "abc", "title": "Hello"}

    expected_repr = "<ContractItem: Hello>"
    expected_natural_key = ("abc",)
    expected_verbose_names = {
        "en": ("contract item", "contract items"),
        "fr": ("contract item", "contract items"),
    }
    expected_fields = {
        "id": models.BigAutoField,
        "slug": models.SlugField,
        "title": models.CharField,
        "is_active": models.BooleanField,
    }
    expected_properties = {
        "upper_title": {"getter_method": "get_upper_title"},
        "lower_title": {"getter_method": "get_lower_title", "cached": True},
    }

    def test_constraint_tests__contractitem__slug_not_empty(self):
        pass


class ContractViolationTests(TestCase):
    """Each variation must make the matching generated test fail."""

    def failures(self, **overrides):
        case = type("Variation", (ContractItemContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_repr(self):
        self.assertEqual(self.failures(expected_repr="<ContractItem: Nope>"), {"test_repr"})

    def test_unexpected_natural_key(self):
        self.assertEqual(self.failures(expected_natural_key=None), {"test_natural_key"})

    def test_wrong_natural_key(self):
        self.assertEqual(self.failures(expected_natural_key=("zzz",)), {"test_natural_key"})

    def test_wrong_verbose_name(self):
        self.assertEqual(
            self.failures(expected_verbose_names={"en": ("other", "contract items")}), {"test_verbose_names"}
        )

    def test_missing_expected_field(self):
        fields = {k: v for k, v in ContractItemContract.expected_fields.items() if k != "title"}
        self.assertEqual(self.failures(expected_fields=fields), {"test_unexpected_fields"})

    def test_extra_expected_field(self):
        fields = {**ContractItemContract.expected_fields, "ghost": models.CharField}
        self.assertEqual(self.failures(expected_fields=fields), {"test_expected_fields"})

    def test_wrong_field_class(self):
        fields = {**ContractItemContract.expected_fields, "title": models.IntegerField}
        self.assertEqual(self.failures(expected_fields=fields), {"test_expected_fields"})

    def test_missing_constraint_test(self):
        self.assertEqual(
            self.failures(test_constraint_tests__contractitem__slug_not_empty=None), {"test_all_constraints_are_tested"}
        )

    def test_undeclared_property(self):
        props = {"upper_title": {"getter_method": "get_upper_title"}}
        self.assertEqual(self.failures(expected_properties=props), {"test_unexpected_properties"})

    def test_wrong_cached_flag(self):
        props = {
            **ContractItemContract.expected_properties,
            "upper_title": {"getter_method": "get_upper_title", "cached": True},
        }
        self.assertEqual(self.failures(expected_properties=props), {"test_property_cached"})

    def test_missing_getter(self):
        props = {**ContractItemContract.expected_properties, "upper_title": {"getter_method": "get_missing"}}
        self.assertEqual(self.failures(expected_properties=props), {"test_property_getters"})

    def test_property_without_getter_check(self):
        props = {**ContractItemContract.expected_properties, "upper_title": {"getter_method": None}}
        self.assertEqual(self.failures(expected_properties=props), set())


class AbstractContractTests(TestCase):
    def test_library_base_class_is_skipped(self):
        result = run_contract(ModelContractTestCase)
        self.assertEqual(result.testsRun, 0)
        self.assertTrue(result.skipped)

    def test_concrete_class_missing_model_is_an_error(self):
        class Forgotten(ModelContractTestCase):
            pass

        result = run_contract(Forgotten)
        self.assertFalse(result.skipped)
        self.assertTrue(result.errors)
