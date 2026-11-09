from private_storage.views import PrivateStorageDetailView

__all__ = [
    "PrivateStorageFileViewer",
]


class PrivateStorageFileViewer(PrivateStorageDetailView):
    """Serve the private file of an object retrieved by a DRF view, through ``django-private-storage``.

    The file is served by the configured ``PRIVATE_STORAGE_SERVER`` (Django, nginx, Apache...) after the
    ``PRIVATE_STORAGE_AUTH_FUNCTION`` check, like ``PrivateStorageDetailView`` does for Django views.
    Needs the ``private-storage`` extra. Usage::

        @action(detail=True)
        def content(self, request, pk=None):
            viewer = PrivateStorageFileViewer(request, self, "content", content_disposition="inline")
            return viewer.get(request)

    Extra keyword arguments (``content_disposition``, ``content_disposition_filename``,
    ``permission_denied_message``...) set the attributes of the same name.
    """

    def __init__(self, request, view, model_file_field="file", **kwargs):
        super().__init__(model_file_field=model_file_field, **kwargs)
        self.request = request
        self.view = view

    def get_object(self, queryset=None):
        return self.view.get_object()
