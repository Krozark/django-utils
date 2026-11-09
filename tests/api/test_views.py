from django.core.files.base import ContentFile
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from ..models import FileItem
from .viewsets import FileItemViewSet


class PrivateFileDownloaderMixinTests(TestCase):
    def setUp(self):
        self.view = FileItemViewSet.as_view({"get": "download"})
        self.factory = APIRequestFactory()

    def test_downloads_the_file_as_an_attachment(self):
        item = FileItem()
        item.file.save("folder/hello.txt", ContentFile(b"hello"), save=True)

        response = self.view(self.factory.get("/"), pk=item.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"hello")
        self.assertEqual(response["Content-Length"], "5")
        self.assertIn('filename="hello', response["Content-Disposition"])
        self.assertTrue(response["Content-Disposition"].startswith("attachment"))

    def test_missing_file_is_a_404(self):
        item = FileItem.objects.create()

        response = self.view(self.factory.get("/"), pk=item.pk)

        self.assertEqual(response.status_code, 404)
