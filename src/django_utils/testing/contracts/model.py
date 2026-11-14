import inspect
from unittest import mock

from django.db import models
from django.utils import translation
from django.utils.functional import cached_property

from ..testcases import TestCase
from .base import ContractMixin

__all__ = ["ModelContractTestCase"]


class ModelContractTestCase(ContractMixin, TestCase):
    """Contract of a model: everything declared in ``expected_*`` must exist and nothing else may.

    - ``factory`` (+ ``build_kwargs``): factory-boy factory building the instance (not saved) used for
      ``expected_repr``, ``expected_natural_key`` and ``expected_properties``; override ``build_instance`` otherwise.
    - ``expected_natural_key``: ``None`` when the model must not define ``natural_key``.
    - ``expected_verbose_names``: ``{language_code: (singular, plural)}``.
    - ``expected_fields``: ``{name: field class}``, checked with ``isinstance``.
    - ``expected_properties``: ``{name: {"getter_method": "get_<name>" (default) or None, "cached": False}}``.
    - Every constraint ``<name>`` needs a ``test_constraint_<name>`` method and must be named
      ``<app_label>__<model_name>__...``.
    """

    required_attributes = ("model",)

    model = None
    factory = None
    build_kwargs = {}
    expected_repr = None
    expected_natural_key = None
    expected_verbose_names = {}
    expected_fields = {}
    expected_properties = {}

    def build_instance(self):
        return self.factory.build(**self.build_kwargs)

    def test_repr(self):
        if self.expected_repr is None:
            self.skipTest("expected_repr is not declared")
        self.assertEqual(repr(self.build_instance()), self.expected_repr)

    def test_natural_key(self):
        if self.expected_natural_key is None:
            self.assertFalse(hasattr(self.model, "natural_key"))
            return
        self.assertTrue(callable(self.model.natural_key))
        self.assertTupleEqual(self.build_instance().natural_key(), self.expected_natural_key)

    def test_verbose_names(self):
        if not self.expected_verbose_names:
            self.skipTest("expected_verbose_names is not declared")
        for language_code, (singular, plural) in self.expected_verbose_names.items():
            with self.subTest(case=language_code), translation.override(language_code):
                self.assertEqual(str(self.model._meta.verbose_name), singular)
                self.assertEqual(str(self.model._meta.verbose_name_plural), plural)

    def test_expected_fields(self):
        field_names = [field.name for field in self.model._meta.fields]
        for name, field_class in self.expected_fields.items():
            with self.subTest(case=name):
                self.assertIn(name, field_names)
                self.assertIsInstance(self.model._meta.get_field(name), field_class)

    def test_unexpected_fields(self):
        for field in self.model._meta.fields:
            with self.subTest(case=field.name):
                self.assertIn(field.name, self.expected_fields)

    def test_all_constraints_are_tested(self):
        for constraint in self.model._meta.constraints:
            with self.subTest(case=constraint.name):
                self.assertTrue(
                    callable(getattr(self, f"test_constraint_{constraint.name}", None)),
                    f"Missing test method test_constraint_{constraint.name}",
                )

    def test_all_constraints_are_properly_named(self):
        prefix = f"{self.model._meta.app_label}__{self.model._meta.model_name}__"
        for constraint in self.model._meta.constraints:
            with self.subTest(case=constraint.name):
                self.assertTrue(
                    constraint.name.startswith(prefix),
                    f"Constraint name '{constraint.name}' does not start with '{prefix}'",
                )

    def _model_properties(self):
        """Properties and cached properties defined by the model itself (Django's own are ignored)."""
        return {
            name: inspect.getattr_static(self.model, name)
            for name in dir(self.model)
            if name not in dir(models.Model)
            and isinstance(inspect.getattr_static(self.model, name), property | cached_property)
        }

    def test_expected_properties(self):
        available = self._model_properties()
        for name in self.expected_properties:
            with self.subTest(case=name):
                self.assertIn(name, available)

    def test_unexpected_properties(self):
        for name in self._model_properties():
            with self.subTest(case=name):
                self.assertIn(name, self.expected_properties)

    def test_property_getters(self):
        for name, options in self.expected_properties.items():
            with self.subTest(case=name):
                self._check_property_getter(name, options.get("getter_method", f"get_{name}"))

    def _check_property_getter(self, name, getter_method):
        if getter_method is None:
            return
        self.assertTrue(callable(getattr(self.model, getter_method, None)), f"'{getter_method}' not found")

        instance = self.build_instance()
        with mock.patch.object(self.model, getter_method) as getter:
            result = getattr(instance, name)
        getter.assert_called_once_with()
        self.assertIs(result, getter.return_value)

    def test_property_cached(self):
        for name, options in self.expected_properties.items():
            with self.subTest(case=name):
                attribute = inspect.getattr_static(self.model, name)
                self.assertIsInstance(attribute, cached_property if options.get("cached", False) else property)
