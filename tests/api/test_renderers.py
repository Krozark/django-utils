import json

from django.test import TestCase
from rest_framework import generics
from rest_framework.test import APIRequestFactory, force_authenticate

from django_utils.api.renderers import HTMXRenderer

from ..helpers import create_user
from ..models import OwnedUUIDItem
from .viewsets import OwnedUUIDItemSerializer, OwnedUUIDItemViewSet


class RendererTestCase(TestCase):
    def setUp(self):
        self.user = create_user()
        self.item = OwnedUUIDItem.objects.create(created_by=self.user)
        self.factory = APIRequestFactory()

    def call(self, action, method="get", path="/items/", data=None, pk=None, **query):
        request = getattr(self.factory, method)(path, data or query, format="json" if data else None)
        force_authenticate(request, self.user)
        kwargs = {"pk": pk} if pk else {}
        response = OwnedUUIDItemViewSet.as_view({method: action})(request, **kwargs)
        response.render()
        return response


class StandardJSONRendererTests(RendererTestCase):
    def test_wraps_successful_responses(self):
        body = json.loads(self.call("list").content)

        self.assertTrue(body["success"])
        self.assertEqual(body["status_code"], 200)
        self.assertEqual(body["message"], "Data retrieved successfully")
        self.assertEqual(body["data"]["pagination"]["count"], 1)
        self.assertIsNone(body["errors"])

    def test_wraps_creation(self):
        response = self.call("create", "post", data={})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content)["message"], "Resource created successfully")

    def test_wraps_errors_raised_as_exceptions(self):
        response = self.call("retrieve", pk=999999)
        body = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual((body["success"], body["data"]), (False, None))
        self.assertEqual(body["errors"], {"error": "No OwnedUUIDItem matches the given query."})

    def test_does_not_wrap_twice(self):
        body = json.loads(self.call("retrieve", pk=999999).content)

        self.assertEqual(set(body), {"success", "status_code", "data", "message", "errors"})
        self.assertIsNone(body["data"])


class HTMXRendererTests(RendererTestCase):
    def test_uses_the_partial_of_the_model_app(self):
        response = self.call("list", format="htmx")

        self.assertEqual(response["Content-Type"], "text/htmx; charset=utf-8")
        self.assertEqual(response.content.decode().strip(), "custom list: 1 items")

    def test_falls_back_to_the_default_partial(self):
        response = self.call("retrieve", pk=self.item.pk, format="htmx")

        self.assertIn(str(self.item.uuid), response.content.decode())

    def test_template_names(self):
        view = OwnedUUIDItemViewSet()
        view.action = "retrieve"

        self.assertEqual(
            HTMXRenderer().get_template_names(None, view),
            ["tests/partials/owneduuiditem_detail_partial.html", "django_utils/htmx/default_partial.html"],
        )

    def test_partials_path_is_configurable(self):
        class SiteRenderer(HTMXRenderer):
            partials_path = "site/partials"

        view = OwnedUUIDItemViewSet()
        view.action = "custom"

        self.assertEqual(
            SiteRenderer().get_template_names(None, view)[0], "site/partials/owneduuiditem_custom_partial.html"
        )


class HTMXRendererEdgeCaseTests(RendererTestCase):
    def test_error_responses_are_rendered_without_fetching_the_object_again(self):
        response = self.call("retrieve", pk=999999, format="htmx")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-Type"], "text/htmx; charset=utf-8")

    def test_views_without_action(self):
        class ListView(generics.ListAPIView):
            queryset = OwnedUUIDItem.objects.all()
            serializer_class = OwnedUUIDItemSerializer

        request = self.factory.get("/items/", {"format": "htmx"})
        force_authenticate(request, self.user)
        response = ListView.as_view()(request)
        response.render()

        self.assertEqual(response.status_code, 200)
