from django.db import models
from django.test import SimpleTestCase

from django_utils.testing import FieldContractTestCase
from tests.models import NotEqual, TagField
from tests.testing.helpers import failed_test_names, run_contract


class TagFieldContract(FieldContractTestCase):
    field_class = TagField
    expected_base_class = models.CharField
    expected_lookups = {**models.CharField.get_lookups(), "ne": NotEqual}
    expected_default_validators = []


class FieldContractViolationTests(SimpleTestCase):
    def failures(self, **overrides):
        case = type("Variation", (TagFieldContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_base_class(self):
        self.assertEqual(self.failures(expected_base_class=models.IntegerField), {"test_base_class"})

    def test_undeclared_lookup(self):
        lookups = {k: v for k, v in TagFieldContract.expected_lookups.items() if k != "ne"}
        self.assertEqual(self.failures(expected_lookups=lookups), {"test_unexpected_lookups"})

    def test_missing_lookup(self):
        lookups = {**TagFieldContract.expected_lookups, "ghost": NotEqual}
        self.assertEqual(self.failures(expected_lookups=lookups), {"test_expected_lookups"})

    def test_wrong_lookup_class(self):
        lookups = {**TagFieldContract.expected_lookups, "ne": models.lookups.Exact}
        self.assertEqual(self.failures(expected_lookups=lookups), {"test_expected_lookups"})

    def test_default_validators(self):
        self.assertEqual(self.failures(expected_default_validators=[len]), {"test_default_validators"})
