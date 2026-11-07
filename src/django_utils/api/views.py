from django.http import FileResponse, Http404
from rest_framework.decorators import action

__all__ = [
    "PrivateFileDownloaderMixin",
]


class PrivateFileDownloaderMixin:
    def get_private_file(self, instance):
        return instance.file

    def get_private_file_name(self, instance, file):
        name = file.name.rsplit("/", 1)[-1]
        return name

    def set_response_header(self, instance, response):
        pass

    @action(
        detail=True,
        methods=["GET"],
    )
    def download(self, request, **kwargs):
        """
        Download the private file.
        """
        obj = self.get_object()
        content_file = self.get_private_file(obj)

        if not content_file:
            raise Http404("File not found")

        filename = self.get_private_file_name(obj, content_file)

        file_handle = content_file.open("rb")
        response = FileResponse(file_handle, as_attachment=True, filename=filename)
        response["Content-Length"] = content_file.size

        self.set_response_header(obj, response)

        return response
