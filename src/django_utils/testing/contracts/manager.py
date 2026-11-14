from ..decorators import with_fixtures
from ..testcases import TestCase
from .base import ContractMixin

__all__ = ["ManagerContractTestCase"]

AVAILABILITY_LOCATIONS = ("manager", "queryset")


class ManagerContractTestCase(ContractMixin, TestCase):
    """Contract of a model manager: class, natural keys and which methods exist on manager and queryset.

    ``expected_natural_keys`` is ``None`` when the manager has no ``get_by_natural_key``, else a list of
    ``{"key": tuple, "instance": index or None}`` (``None``: the key must not match) where indexes refer to
    ``self.instances``, filled by ``fixtures_expected_natural_keys``.
    ``expected_method_availabilities`` maps a method name to ``{"manager": bool, "queryset": bool}``.
    """

    required_attributes = ("model", "expected_manager_class")

    model = None
    manager_name = "objects"
    expected_manager_class = None
    expected_natural_keys = None
    expected_method_availabilities = {}
    instances = []

    @property
    def manager(self):
        return getattr(self.model, self.manager_name)

    def test_manager_class(self):
        self.assertIsInstance(self.manager, self.expected_manager_class)

    def test_natural_key_availability(self):
        self.assertEqual(hasattr(self.manager, "get_by_natural_key"), self.expected_natural_keys is not None)

    def fixtures_expected_natural_keys(self):
        pass

    @with_fixtures()
    def test_expected_natural_keys(self):
        for case in self.expected_natural_keys or []:
            with self.subTest(case=case["key"]):
                if case["instance"] is None:
                    with self.assertRaises(self.model.DoesNotExist):
                        self.manager.get_by_natural_key(*case["key"])
                else:
                    instance = self.manager.get_by_natural_key(*case["key"])
                    self.assertEqual(instance.pk, self.instances[case["instance"]].pk)

    def test_method_availabilities(self):
        for method_name, availabilities in self.expected_method_availabilities.items():
            for location in AVAILABILITY_LOCATIONS:
                with self.subTest(case=f"{method_name}_from_{location}"):
                    self.assertIn(location, availabilities, f"Missing '{location}' for '{method_name}'")
                    target = self.manager.all() if location == "queryset" else self.manager
                    self.assertEqual(hasattr(target, method_name), availabilities[location])
