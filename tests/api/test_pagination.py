from django.test import TestCase
from rest_framework.test import APIRequestFactory

from ..helpers import create_user
from ..models import OwnedUUIDItem
from .viewsets import OwnedUUIDItemViewSet


class StandardResultsSetPaginationTests(TestCase):
    def setUp(self):
        user = create_user()
        OwnedUUIDItem.objects.bulk_create([OwnedUUIDItem(created_by=user) for _ in range(5)])
        self.view = OwnedUUIDItemViewSet.as_view({"get": "list"})
        self.factory = APIRequestFactory()

    def test_paginated_response_shape(self):
        data = self.view(self.factory.get("/items/")).data

        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(
            data["pagination"],
            {
                "count": 5,
                "next": "http://testserver/items/?page=2",
                "previous": None,
                "page_size": 2,
                "current_page": 1,
                "total_pages": 3,
            },
        )

    def test_page_size_is_capped(self):
        data = self.view(self.factory.get("/items/", {"page_size": 100})).data

        self.assertEqual(data["pagination"]["page_size"], 25)
        self.assertEqual(len(data["results"]), 5)
