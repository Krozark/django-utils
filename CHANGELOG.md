# Changelog

## Unreleased

First release candidate. Content:

- Initial project skeleton.
- Add model mixins (`UUIDMixin`, `CreatedByMixin`, `IsPublicMixin`, `AutoVersionFieldMixin`, `StorageSizeMixin`, `SoftDeletionMixin`, `ClassRegistryMixin`).
- Add admin mixins (`CreatedByAdminMixin`, `IsPublicAdminMixin`, `ReadOnlyAdminMixin`), `FileSizeField` and helpers (`md5_checksum`, `set_m2m`, `lookup_by_uuid`, `get_model_permission`).
- Add `django_utils.api` (extra `drf`): permissions, serializer mixins, standard response envelope (renderer and exception handler), HTMX renderer, pagination, `UUIDInFilter`, `PrivateFileDownloaderMixin`.
- Add `django_utils.gating`: gated features registry and system checks, `ExtraPermissionsBackend`, `{% gated_block %}` template tag, `GatedFieldsSerializerMixin` and `GatedFeaturesView`.
- Add `PermissionCacheMixin` and `AbstractSubscriptionPlan`.
- Add `DryRunCommand` and `CleanupCommand`, `SoftDeletionMixin.get_expired()`, `rsa_keys` (extra `crypto`) and `PrivateStorageFileViewer` (extra `private-storage`).
- Add the `language_flag` template filter (`django_utils_tags`).
