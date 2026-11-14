from rest_framework.fields import empty

from ..contracts.base import ContractMixin
from ..decorators import with_fixtures
from ..testcases import TestCase
from .requests import RequestBuilderMixin

__all__ = ["SerializerContractTestCase"]


class SerializerContractTestCase(ContractMixin, RequestBuilderMixin, TestCase):
    """Contract of a DRF serializer: its fields, which ones are readable/writable/required, its output and errors.

    - ``expected_fields``: ``{name: field class}``, compared with the exact class.
    - ``expected_readable_fields`` / ``expected_writable_fields`` / ``expected_required_fields``: sets of names.
    - ``expected_representations``: list of ``{"instance": index | "instances": [indexes], "expected": data,
      "user": key, "query_params": dict, "serializer_kwargs": dict, "name": label}``.
    - ``expected_validation_errors``: list of ``{"data": dict, "errors": dict, "instance": index, "user": key,
      "partial": bool}``.

    Indexes refer to ``self.instances`` and users to ``self.users``; both are built by ``create_fixtures``.
    """

    required_attributes = ("serializer_class",)

    serializer_class = None
    expected_fields = {}
    expected_readable_fields = set()
    expected_writable_fields = set()
    expected_required_fields = set()
    expected_representations = []
    expected_validation_errors = []

    def build_serializer(self, *args, user_key=None, query_params=None, **kwargs):
        user = self.users[user_key] if user_key is not None else None
        request = self.build_request(query_params=query_params, user=user)
        return self.serializer_class(*args, context={"request": request}, **kwargs)

    @property
    def fields(self):
        return self.build_serializer().fields

    def test_expected_fields(self):
        fields = self.fields
        for name, field_class in self.expected_fields.items():
            with self.subTest(case=name):
                self.assertIn(name, fields)
                self.assertIs(type(fields[name]), field_class)

    def test_unexpected_fields(self):
        for name in self.fields:
            with self.subTest(case=name):
                self.assertIn(name, self.expected_fields)

    def test_readable_fields(self):
        readable = {name for name, field in self.fields.items() if not field.write_only}
        self.assertSetEqual(readable, set(self.expected_readable_fields))

    def test_writable_fields(self):
        self.assertSetEqual(self._writable_field_names(), set(self.expected_writable_fields))

    def test_required_fields(self):
        required = {name for name in self._writable_field_names() if self.fields[name].required}
        self.assertSetEqual(required, set(self.expected_required_fields))

    def _writable_field_names(self):
        return {name for name, field in self.fields.items() if not field.read_only or field.default is not empty}

    def fixtures_expected_representations(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_representations(self):
        for index, case in enumerate(self.expected_representations):
            with self.subTest(case=case.get("name", index)):
                self._check_representation(case)

    def _check_representation(self, case):
        if "instances" in case:
            instance, kwargs = [self.instances[i] for i in case["instances"]], {"many": True}
        else:
            instance, kwargs = self.instances[case["instance"]], {}

        serializer = self.build_serializer(
            instance,
            user_key=case.get("user"),
            query_params=case.get("query_params"),
            **kwargs,
            **case.get("serializer_kwargs", {}),
        )
        self.assertEqual(serializer.data, case["expected"])

    def fixtures_expected_validation_errors(self):
        self.create_fixtures()

    @with_fixtures()
    def test_expected_validation_errors(self):
        for index, case in enumerate(self.expected_validation_errors):
            with self.subTest(case=case.get("name", index)):
                instance = self.instances[case["instance"]] if case.get("instance") is not None else None
                serializer = self.build_serializer(
                    instance, user_key=case.get("user"), data=case["data"], partial=case.get("partial", False)
                )
                serializer.is_valid()
                self.assertEqual(serializer.errors, case["errors"])
