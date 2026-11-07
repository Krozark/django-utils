# Changelog

## Unreleased

- Initial project skeleton.
- Add model mixins (`UUIDMixin`, `CreatedByMixin`, `IsPublicMixin`, `AutoVersionFieldMixin`, `StorageSizeMixin`, `SoftDeletionMixin`, `ClassRegistryMixin`).
- Add admin mixins (`CreatedByAdminMixin`, `IsPublicAdminMixin`, `ReadOnlyAdminMixin`), `FileSizeField` and helpers (`md5_checksum`, `set_m2m`, `lookup_by_uuid`, `get_model_permission`).
- Add `django_utils.api` (extra `drf`): permissions, serializer mixins, standard response envelope (renderer and exception handler), HTMX renderer, pagination, `UUIDInFilter`, `PrivateFileDownloaderMixin`.
