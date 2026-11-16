from django.test import SimpleTestCase
from rest_framework.request import Request

from django_utils.testing.api import RequestBuilderMixin
from tests.testing.factories import UserFactory


class RequestBuilderMixinTests(RequestBuilderMixin, SimpleTestCase):
    def test_wsgi_request_uses_method_path_and_query_params(self):
        request = self.build_wsgi_request(method="POST", path="/items/", query_params={"a": "1", "b": "x y"})

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_full_path(), "/items/?a=1&b=x+y")

    def test_request_is_a_drf_request(self):
        request = self.build_request(query_params={"page": "2"})

        self.assertIsInstance(request, Request)
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.query_params["page"], "2")

    def test_request_is_forced_authenticated(self):
        user = UserFactory.build(username="john")

        request = self.build_request(user=user)

        self.assertEqual(request.user, user)

    def test_request_is_anonymous_without_user(self):
        self.assertFalse(self.build_request().user.is_authenticated)
