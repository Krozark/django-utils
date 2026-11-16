from ..testcases import SimpleTestCase
from .base import ContractMixin

__all__ = ["FieldContractTestCase"]


class FieldContractTestCase(ContractMixin, SimpleTestCase):
    """Contract of a custom model field: base class, registered lookups and default validators."""

    required_attributes = ("field_class", "expected_base_class")

    field_class = None
    expected_base_class = None
    expected_lookups = {}
    expected_default_validators = []

    def test_base_class(self):
        self.assertTrue(issubclass(self.field_class, self.expected_base_class))

    def test_expected_lookups(self):
        available_lookups = self.field_class.get_lookups()
        for name, lookup_class in self.expected_lookups.items():
            with self.subTest(case=name):
                self.assertIn(name, available_lookups)
                self.assertEqual(available_lookups[name], lookup_class)

    def test_unexpected_lookups(self):
        for name in self.field_class.get_lookups():
            with self.subTest(case=name):
                self.assertIn(name, self.expected_lookups)

    def test_default_validators(self):
        self.assertCountEqual(self.field_class.default_validators, self.expected_default_validators)
