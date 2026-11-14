from contextlib import nullcontext

from django.test import SimpleTestCase, TestCase

from django_utils.testing import subtests_cases, with_fixtures
from tests.models import VersionedItem


class SubtestsCasesTests(TestCase):
    seen = []

    @subtests_cases({"first": [1], "second": [2], "tuple": (3, 4)})
    def test_plain_cases_receive_their_data(self, data):
        self.seen.append(data)

    def test_every_case_ran(self):
        self.seen.clear()
        self.test_plain_cases_receive_their_data()
        self.assertEqual(self.seen, [[1], [2], (3, 4)])

    @subtests_cases({"a": [1], "b": [1], "c": [1]})
    def test_database_is_rolled_back_between_cases(self, data):
        VersionedItem.objects.create(name="x")
        self.assertEqual(VersionedItem.objects.count(), 1)

    @subtests_cases({"raises": {"data": ["boom"], "raises": ValueError}})
    def test_expected_exception(self, data):
        raise ValueError(data[0])

    @subtests_cases({"raises": {"data": ["boom"], "raises": ValueError, "message": "boom"}})
    def test_expected_exception_message(self, data):
        raise ValueError(data[0])

    @subtests_cases({"ok": {"data": [5]}})
    def test_dict_case_without_exception(self, data):
        self.assertEqual(data, [5])

    def test_wrong_exception_message_fails(self):
        @subtests_cases({"wrong": {"data": [], "raises": ValueError, "message": "expected"}})
        def case(test, data):
            raise ValueError("other")

        with self.assertRaises(self.failureException):
            self.subTest = _FailFast(self)
            case(self)

    def test_expected_exception_not_raised_fails(self):
        @subtests_cases({"silent": {"data": [], "raises": ValueError}})
        def case(test, data):
            pass

        with self.assertRaises(self.failureException):
            self.subTest = _FailFast(self)
            case(self)

    def test_unknown_case_key_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "unknown"):
            subtests_cases({"bad": {"data": [], "expected_exception": ValueError}})

    def test_case_without_data_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "data"):
            subtests_cases({"bad": {"raises": ValueError}})


class _FailFast:
    """Replacement for ``subTest`` that lets failures propagate instead of being recorded."""

    def __init__(self, test):
        self.test = test

    def __call__(self, **kwargs):
        return nullcontext()


class WithFixturesTests(SimpleTestCase):
    def setUp(self):
        self.prepared = None

    def fixtures_method(self):
        self.prepared = "default"

    def fixtures_custom(self):
        self.prepared = "custom"

    @with_fixtures()
    def test_method(self):
        self.assertEqual(self.prepared, "default")

    @with_fixtures("fixtures_custom")
    def test_explicit_method(self):
        self.assertEqual(self.prepared, "custom")

    def test_missing_fixtures_method(self):
        @with_fixtures()
        def test_ghost(test):
            pass

        with self.assertRaisesMessage(AttributeError, "fixtures_ghost"):
            test_ghost(self)

    def test_arguments_are_forwarded(self):
        @with_fixtures("fixtures_method")
        def test_args(test, value):
            return (test.prepared, value)

        self.assertEqual(test_args(self, 7), ("default", 7))
