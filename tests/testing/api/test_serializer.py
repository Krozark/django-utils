from django.test import TestCase
from rest_framework import serializers

from django_utils.testing.api import SerializerContractTestCase
from tests.testing.api.viewsets import ContractItemSerializer
from tests.testing.factories import ContractItemFactory, UserFactory
from tests.testing.helpers import failed_test_names, run_contract


class ContractItemSerializerContract(SerializerContractTestCase):
    serializer_class = ContractItemSerializer
    users = {"admin": lambda: UserFactory(is_staff=True)}

    expected_fields = {
        "id": serializers.IntegerField,
        "slug": serializers.SlugField,
        "title": serializers.CharField,
        "is_active": serializers.BooleanField,
    }
    expected_readable_fields = {"id", "slug", "title", "is_active"}
    expected_writable_fields = {"slug", "title", "is_active"}
    expected_required_fields = {"slug", "title"}
    expected_representations = [
        {"instance": 0, "expected": {"id": 1, "slug": "first", "title": "Alpha", "is_active": True}},
        {
            "name": "many as admin",
            "instances": [0, 1],
            "user": "admin",
            "expected": [
                {"id": 1, "slug": "first", "title": "Alpha", "is_active": True},
                {"id": 2, "slug": "second", "title": "Bravo", "is_active": False},
            ],
        },
    ]
    expected_validation_errors = [
        {"data": {"title": "x"}, "errors": {"slug": ["This field is required."]}},
        {
            "data": {"slug": "first", "title": "x"},
            "errors": {"slug": ["contract item with this slug already exists."]},
            "user": "admin",
        },
        {"data": {"slug": "second"}, "instance": 1, "partial": True, "errors": {}},
    ]

    def create_fixtures(self):
        self.instances = [
            ContractItemFactory(pk=1, slug="first", title="Alpha"),
            ContractItemFactory(pk=2, slug="second", title="Bravo", is_active=False),
        ]


class SerializerContractViolationTests(TestCase):
    def failures(self, **overrides):
        case = type("Variation", (ContractItemSerializerContract,), overrides)
        return failed_test_names(run_contract(case))

    def test_valid_contract_passes(self):
        self.assertEqual(self.failures(), set())

    def test_wrong_field_class(self):
        fields = {**ContractItemSerializerContract.expected_fields, "title": serializers.IntegerField}
        self.assertEqual(self.failures(expected_fields=fields), {"test_expected_fields"})

    def test_undeclared_field(self):
        fields = {k: v for k, v in ContractItemSerializerContract.expected_fields.items() if k != "title"}
        self.assertEqual(self.failures(expected_fields=fields), {"test_unexpected_fields"})

    def test_missing_field(self):
        fields = {**ContractItemSerializerContract.expected_fields, "ghost": serializers.CharField}
        self.assertEqual(self.failures(expected_fields=fields), {"test_expected_fields"})

    def test_readable_fields(self):
        self.assertEqual(self.failures(expected_readable_fields={"id", "slug", "title"}), {"test_readable_fields"})
        self.assertEqual(
            self.failures(expected_readable_fields={"id", "slug", "title", "is_active", "ghost"}),
            {"test_readable_fields"},
        )

    def test_writable_fields(self):
        self.assertEqual(self.failures(expected_writable_fields={"slug", "title"}), {"test_writable_fields"})
        self.assertEqual(
            self.failures(expected_writable_fields={"slug", "title", "is_active", "id"}), {"test_writable_fields"}
        )

    def test_required_fields(self):
        self.assertEqual(self.failures(expected_required_fields={"slug"}), {"test_required_fields"})
        self.assertEqual(
            self.failures(expected_required_fields={"slug", "title", "is_active"}), {"test_required_fields"}
        )

    def test_wrong_representation(self):
        representations = [{"instance": 0, "expected": {"id": 1}}]
        self.assertEqual(self.failures(expected_representations=representations), {"test_expected_representations"})

    def test_wrong_validation_errors(self):
        errors = [{"data": {"title": "x"}, "errors": {}}]
        self.assertEqual(self.failures(expected_validation_errors=errors), {"test_expected_validation_errors"})
