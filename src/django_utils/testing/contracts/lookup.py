from ..decorators import with_fixtures
from ..testcases import TestCase
from .base import ContractMixin

__all__ = ["LookupContractTestCase"]


class LookupContractTestCase(ContractMixin, TestCase):
    """Contract of a custom lookup, checked through a model field using it.

    ``expected_querysets`` is a list of ``{"value": ..., "instances": [indexes]}`` (optionally ``"ordered": True``)
    or ``{"value": ..., "raises": ExceptionClass}``. Indexes refer to ``self.instances``, filled by
    ``fixtures_expected_querysets``.
    """

    required_attributes = ("lookup_class", "model")

    lookup_class = None
    model = None
    lookup_field_name = "field"
    expected_lookup_name = ""
    expected_querysets = []
    instances = []

    def test_lookup_name(self):
        self.assertEqual(self.lookup_class.lookup_name, self.expected_lookup_name)

    def fixtures_expected_querysets(self):
        pass

    @with_fixtures()
    def test_expected_querysets(self):
        for case in self.expected_querysets:
            with self.subTest(case=repr(case["value"])):
                self._check_queryset(case)

    def _check_queryset(self, case):
        filters = {f"{self.lookup_field_name}__{self.expected_lookup_name}": case["value"]}

        if "raises" in case:
            with self.assertRaises(case["raises"]):
                list(self.model.objects.filter(**filters))
            return

        expected = [self.instances[index] for index in case["instances"]]
        self.assertQuerySetEqual(self.model.objects.filter(**filters), expected, ordered=case.get("ordered", False))
