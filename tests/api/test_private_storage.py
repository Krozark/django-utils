from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.test import APIRequestFactory, force_authenticate

from django_utils.api.private_storage import PrivateStorageFileViewer

from ..helpers import create_user
from ..models import PrivateFileItem


class PrivateFileItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PrivateFileItem.objects.all()

    @action(detail=True)
    def content(self, request, pk=None):
        return PrivateStorageFileViewer(request, self, "file", content_disposition="inline").get(request)


class PrivateStorageFileViewerTests(TestCase):
    def setUp(self):
        self.item = PrivateFileItem()
        self.item.file.save("hello.txt", ContentFile(b"hello"), save=True)
        self.view = PrivateFileItemViewSet.as_view({"get": "content"})
        self.factory = APIRequestFactory()

    def get(self, user=None, pk=None):
        request = self.factory.get("/")
        if user:
            force_authenticate(request, user)
        return self.view(request, pk=pk or self.item.pk)

    def test_serves_the_file_to_authorized_users(self):
        response = self.get(create_user())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"hello")
        self.assertTrue(response["Content-Disposition"].startswith("inline; filename"))
        self.assertIn("hello", response["Content-Disposition"])

    def test_denies_other_users(self):
        self.assertEqual(self.get().status_code, 403)

    def test_missing_file_is_a_404(self):
        self.item.file.storage.delete(self.item.file.name)

        self.assertEqual(self.get(create_user()).status_code, 404)

    def test_unknown_object_is_a_404(self):
        self.assertEqual(self.get(create_user(), pk=999999).status_code, 404)
