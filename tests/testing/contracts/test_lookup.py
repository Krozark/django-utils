from django.test import SimpleTestCase

from django_utils.testing import LookupContractTestCase
from tests.models import NotEqual, TaggedItem
from tests.testing.factories import TaggedItemFactory
from tests.testing.helpers import failed_test_names, run_contract


class NotEqualContract(LookupContractTestCase):
    lookup_class = NotEqual
    model = TaggedItem
    lookup_field_name = "tag"
    expected_lookup_name = "ne"
    expected_querysets = [
        {"value": "a", "instances": [1, 2]},
        {"value": "zzz", "instances": [0, 1, 2]},
        {"value": "a", "instances": [1, 2], "ordered": False},
        {"value": object(), "raises": TypeError},
    ]

    def fixtures_expected_querysets(self):
        self.instances = [TaggedItemFactory(tag=tag) for tag in ("a", "b", "c")]


class LookupContractViolationTests(SimpleTestCase):
    def failures(self, **overrides):
        case = type("Variation", (NotEqualContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_lookup_name(self):
        self.assertEqual(self.failures(expected_lookup_name="other"), {"test_lookup_name"})

    def test_wrong_queryset(self):
        self.assertEqual(
            self.failures(expected_querysets=[{"value": "a", "instances": [0]}]), {"test_expected_querysets"}
        )

    def test_expected_exception_not_raised(self):
        self.assertEqual(
            self.failures(expected_querysets=[{"value": "a", "raises": TypeError}]), {"test_expected_querysets"}
        )
