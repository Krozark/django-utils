# Changelog

## Unreleased

- Drop Django 5.0 and 5.1: Django 5.2 or later is required.
- Add `django_utils.testing` (extra `testing`): `TestCase`/`SimpleTestCase` with frozen time, media cleanup and
  factory-friendly `users`, `subtests_cases`, `with_fixtures`, `rollback_atomic`, and contract test cases for models,
  fields, lookups and managers. `django_utils.testing.api` (also needs `drf`) adds contract test cases for
  serializers, filtersets and viewsets, and `RequestBuilderMixin`.
- `StorageSizeMixin.save(update_fields=None)` raised a `TypeError`: `None` ("save every field") is now passed through,
  like `AutoVersionFieldMixin` does.
- Add `is_safe_redirect_url(request, url)`: whether a `?next=` target stays on the site.
- `format_errors` kept only one message when the error data had both `detail` and `non_field_errors`.
- `HTMXRenderer` crashed on an error response when the view could not build its queryset (anonymous request on a
  queryset filtered on the user): it falls back to the default partial.

## 26.11.09 — 2026-11-09

First release. Content:

- Initial project skeleton.
- Add model mixins (`UUIDMixin`, `CreatedByMixin`, `IsPublicMixin`, `AutoVersionFieldMixin`, `StorageSizeMixin`, `SoftDeletionMixin`, `ClassRegistryMixin`).
- Add admin mixins (`CreatedByAdminMixin`, `IsPublicAdminMixin`, `ReadOnlyAdminMixin`), `FileSizeField` and helpers (`md5_checksum`, `set_m2m`, `lookup_by_uuid`, `get_model_permission`).
- Add `django_utils.api` (extra `drf`): permissions, serializer mixins, standard response envelope (renderer and exception handler), HTMX renderer, pagination, `UUIDInFilter`, `PrivateFileDownloaderMixin`.
- Add `django_utils.gating`: gated features registry and system checks, `ExtraPermissionsBackend`, `{% gated_block %}` template tag, `GatedFieldsSerializerMixin` and `GatedFeaturesView`.
- Add `PermissionCacheMixin` and `AbstractSubscriptionPlan`.
- Add `DryRunCommand` and `CleanupCommand`, `SoftDeletionMixin.get_expired()`, `rsa_keys` (extra `crypto`) and `PrivateStorageFileViewer` (extra `private-storage`).
- Add the `language_flag` template filter (`django_utils_tags`).

### Fixed during the review

- `ClassRegistryMixin` crashed on abstract roots and could register abstract models: it now registers through
  `class_prepared` (and ignores the historical models of the migrations).
- `AutoVersionFieldMixin` bumped the version when an object with a known primary key was created, and lost the
  bump when saving with `update_fields`.
- `IsPublicAdminMixin` ignored the other admin mixins' `get_queryset()`: combined with `CreatedByAdminMixin` in
  this order, users could list the objects of the others.
- `HTMXRenderer` failed on error responses of `retrieve` and on views without `action`.
- Nested validation errors are flattened into readable messages (they used to be Python reprs).
- `gated_features` given as a string is reported by the system check (it used to be read character by character).
- `FileSizeField` accepts a decimal comma (`1,5GB`); `set_m2m` rejects unknown modes; `__version__` no longer
  fails when the package is not installed; `ensure_dev_keys` replaces existing key files on every platform.
- `lookup_by_uuid` returns `(None, False)` for a malformed UUID instead of raising.
- `StandardJSONRenderer` leaves 204/304 responses empty (they used to carry a JSON body, which HTTP forbids).
- `CreatedByMixin.get_created_at_display()` is localized (`created_at_display_format`, `"SHORT_DATETIME_FORMAT"` by default).
