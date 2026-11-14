from ..contracts.base import ContractMixin
from ..testcases import TestCase
from .requests import RequestBuilderMixin

__all__ = ["FilterSetContractTestCase"]


class FilterSetContractTestCase(ContractMixin, RequestBuilderMixin, TestCase):
    """Contract of a django-filter ``FilterSet``: its filters, each of which needs a ``test_filter_<name>`` method.

    ``expected_filters`` maps a filter name to a filter class, or to a tuple of classes the filter must all be
    an instance of. Write the filter tests with ``assert_filter``.
    """

    required_attributes = ("filterset_class",)

    filterset_class = None
    expected_filters = {}

    def test_expected_filters(self):
        available = self.filterset_class.base_filters
        for name, filter_classes in self.expected_filters.items():
            with self.subTest(case=name):
                self.assertIn(name, available)
                if not isinstance(filter_classes, tuple | list):
                    filter_classes = [filter_classes]
                for filter_class in filter_classes:
                    self.assertIsInstance(available[name], filter_class)

    def test_unexpected_filters(self):
        for name in self.filterset_class.base_filters:
            with self.subTest(case=name):
                self.assertIn(name, self.expected_filters)

    def test_all_filters_are_tested(self):
        for name in self.expected_filters:
            with self.subTest(case=name):
                self.assertTrue(callable(getattr(self, f"test_filter_{name}", None)), f"Missing test_filter_{name}")

    def assert_filter(self, filter_name, *, data, user=None, queryset=None, expected_instances=(), expected_errors=()):
        """Apply the filterset to ``data`` (as ``users[user]``) and check the instances kept and the errors of
        ``filter_name``. Instances are indexes in ``self.instances``; the order is not checked.
        """
        if queryset is None:
            queryset = self.filterset_class._meta.model._default_manager.all()
        request_user = self.users[user] if user is not None else None
        filterset = self.filterset_class(data=data, queryset=queryset, request=self.build_request(user=request_user))

        self.assertQuerySetEqual(filterset.qs, [self.instances[i] for i in expected_instances], ordered=False)
        self.assertListEqual(list(filterset.errors.get(filter_name, [])), list(expected_errors))
