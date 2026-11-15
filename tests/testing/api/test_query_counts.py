from django.test import TestCase, override_settings

from django_utils.testing import TestCase as FrameworkTestCase
from django_utils.testing.api import QueryCountMixin
from tests.testing.factories import ContractItemFactory, UserFactory
from tests.testing.helpers import run_contract


@override_settings(ROOT_URLCONF="tests.testing.api.urls")
class QueryCountMixinTests(QueryCountMixin, FrameworkTestCase):
    def setUp(self):
        self.client.force_authenticate(user=UserFactory(is_staff=True))
        ContractItemFactory(slug="first")

    def create(self):
        return ContractItemFactory()

    def test_paginated_list_default_budget(self):
        self.assert_query_count("/items/", self.create)

    def test_detail_default_budget(self):
        self.assert_query_count("/items/first/", self.create)

    def test_explicit_budget(self):
        self.assert_query_count("/items/titles/", self.create, expected=1)

    def test_wrong_budget_fails(self):
        with self.assertRaisesMessage(self.failureException, "expected 5 queries"):
            self.assert_query_count("/items/", self.create, expected=5)

    def test_n_plus_one_fails_and_lists_the_repeated_queries(self):
        with self.assertRaisesMessage(self.failureException, "more:"):
            self.assert_query_count("/n-plus-one/", self.create, expected=3)

    def test_error_response_fails(self):
        with self.assertRaises(self.failureException):
            self.assert_query_count("/items/missing/", self.create)

    def test_creation_callback_runs_before_each_measure(self):
        created = []
        self.assert_query_count("/items/", lambda: created.append(self.create()))
        self.assertEqual(len(created), 3)


@override_settings(ROOT_URLCONF="tests.testing.api.urls")
class QueryCountsCasesTests(TestCase):
    def run_cases(self, cases):
        class Cases(QueryCountMixin, FrameworkTestCase):
            def setUp(self):
                self.client.force_authenticate(user=UserFactory(is_staff=True))

            def test_cases(self):
                self.assert_query_counts(cases)
                self.leftover = ContractItemFactory._meta.model.objects.count()
                self.assertEqual(self.leftover, 0)

        return run_contract(Cases)

    def test_each_case_is_checked_and_rolled_back(self):
        result = self.run_cases(
            {
                "/items/": ContractItemFactory,
                "/items/titles/": (ContractItemFactory, 1),
            }
        )
        self.assertEqual((result.failures, result.errors), ([], []))

    def test_a_failing_case_is_reported(self):
        result = self.run_cases({"/n-plus-one/": (ContractItemFactory, 3)})
        self.assertEqual(len(result.failures), 1)
