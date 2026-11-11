# django-utils

Reusable Django utilities shared across projects: model and admin mixins, form fields, helpers, Django REST
framework building blocks, and a small framework to reserve features to some users ("gated features").

Everything here is project-agnostic. Project-specific behaviour is plugged in through hooks (methods to override,
settings, overridable templates), never through imports of the project.

## Installation

```bash
uv add "django-utils @ git+https://github.com/Krozark/django-utils.git@26.11.09"
```

Versions are calendar-based (`YY.MM.DD`) and tagged.

Optional features come with extras, for instance
`uv add "django-utils[drf,crypto] @ git+https://github.com/Krozark/django-utils.git"`:

| Extra | For |
|---|---|
| `drf` | the REST framework helpers (`django_utils.api`) |
| `private-storage` | `django_utils.api.private_storage` (also needs DRF) |
| `crypto` | `django_utils.rsa_keys` |

Then add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "django_utils",
]
```

Compatible with Django 5.0+ and 6.x, Python 3.12+.

## Layout

```
src/django_utils/
├── models/          # mixins.py (UUID, created by, public, version, storage, soft deletion, registry,
│                    #            permission cache) and subscription.py (AbstractSubscriptionPlan)
├── admin.py         # admin mixins
├── forms/fields.py  # FileSizeField
├── utils.py         # helpers
├── rsa_keys.py      # (extra "crypto") RSA key pairs from the environment, generated in development
├── management/      # base.py: DryRunCommand, CleanupCommand
├── gating/          # registry, system checks, ExtraPermissionsBackend
├── templatetags/    # django_utils_gating ({% gated_block %}), django_utils_tags (language_flag)
├── templates/       # default templates, all under django_utils/
└── api/             # (extra "drf") permissions, serializers, envelope, renderers, handlers,
                     # pagination, filters, views, private_storage
```

## Model mixins

`django_utils.models` provides abstract models and helpers:

| Name | Purpose |
|---|---|
| `UUIDMixin` | `uuid` field (not the primary key) |
| `CreatedByMixin` | `created_by` FK to the user model + `created_at` / `updated_at` |
| `IsPublicMixin` | `is_public` flag + `manager_public` manager |
| `VersionFieldMixin` / `AutoVersionFieldMixin` | `version` counter, auto-incremented when a field changes |
| `StorageSizeMixin` | `storage_size` in bytes, refreshed on each save through `update_size()` |
| `SoftDeletionMixin` | soft delete with a grace period; `get_expired()` returns what can be hard-deleted |
| `ClassRegistryMixin` | self-registration of the concrete models inheriting from the class that holds the registry |
| `PermissionCacheMixin` | for user models: `clear_permission_cache()` after the permissions of a user changed |
| `AbstractSubscriptionPlan` | abstract plan with `groups` and `user_permissions`; `get_permissions()` feeds an `ExtraPermissionsBackend` (several concrete plan models can coexist) |

## Admin, forms and helpers

- `django_utils.admin`: `CreatedByAdminMixin` (users only see and edit their own objects, with a username filter),
  `IsPublicAdminMixin`, `ReadOnlyAdminMixin`. The username filter uses a template shipped with the app, so
  `django_utils` must be in `INSTALLED_APPS`.
- `django_utils.forms.FileSizeField` (`forms/fields.py`): accepts `100MB`, `1 GB`... and cleans to bytes.
- `django_utils.utils`: `md5_checksum`, `set_m2m`, `lookup_by_uuid`, `get_model_permission`.
- `django_utils.management.base`: `DryRunCommand` (a `--dry-run` option, `self.dry_run`) and `CleanupCommand`
  (deletes the objects of `get_queryset()`, with `--dry-run` and a report).
- `django_utils.rsa_keys` (extra `crypto`): `load_rsa_key_pair()` reads a PEM key pair from environment variables;
  `ensure_dev_keys()` generates and stores the missing ones in `.env` for development.

## REST framework (`django_utils.api`, extra `drf`)

| Module | Content |
|---|---|
| `permissions` | `FullModelPermissions` (view permission required on GET), `AllowNone`, `IsSuperuser`, `CurrentUser`, `CurrentUserOrSuperuser`, `CurrentUserOrSuperuserOrReadOnly`, `CreatedByObjectPermission` |
| `serializers` | `UUIDMixinSerializer`, `CreatedByMixinSerializer`, `CreatedByAndUUIDMixinSerializer`, `RequestUserSerializerMixin` (`check_user`, `check_perm`) |
| `envelope`, `renderers`, `handlers` | standard response `{success, status_code, data, message, errors}`: `StandardJSONRenderer` and `custom_exception_handler`; `HTMXRenderer` returns HTML partials for `?format=htmx` |
| `pagination` | `StandardResultsSetPagination` (`{results, pagination}`) |
| `filters` | `UUIDInFilter` (comma-separated UUIDs) |
| `views` | `PrivateFileDownloaderMixin` (`download` action), `GatedFeaturesView` |
| `private_storage` | `PrivateStorageFileViewer`: serves the private file of an object through `django-private-storage` (extra `private-storage`) |

```python
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "django_utils.api.renderers.StandardJSONRenderer",
        "django_utils.api.renderers.HTMXRenderer",
    ],
    "EXCEPTION_HANDLER": "django_utils.api.handlers.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "django_utils.api.pagination.StandardResultsSetPagination",
}
```

`HTMXRenderer` looks for `<app_label>/partials/<model>_<list|detail|form|action>_partial.html` and falls back to
`django_utils/htmx/default_partial.html`. Subclass it to change `partials_path`.

## Gated features (`django_utils.gating`)

A gated feature is a Django permission reserved for some users (e.g. a subscription plan). Models declare theirs:

```python
class Ambience(models.Model):
    gated_features = ["my_app.set_on_start"]

    class Meta:
        permissions = [("set_on_start", "Can set the on_start of an ambience")]
```

- A system check (`django_utils.E001` to `E003`) rejects malformed, unknown or ambiguous entries.
- `get_user_gated_features(user)` returns `{"set_on_start": True/False}` (`GatedFeaturesView` serves it as JSON).
- `ExtraPermissionsBackend` is a `ModelBackend` with one hook, `get_extra_permissions(user)`, to grant permissions
  coming from elsewhere (a subscription for instance). Add the subclass to `AUTHENTICATION_BACKENDS`.
- `{% load django_utils_gating %}{% gated_block "set_on_start" %}...{% endgated_block %}` renders Alpine.js
  `x-if="permissions.set_on_start"` branches, with a locked message as fallback. Override
  `django_utils/gating/gated_block.html` to change the markup or the message.
- `GatedFieldsSerializerMixin` (extra `drf`): `gated_fields = {"on_start": "my_app.set_on_start"}` makes the serializer
  refuse non-empty values for these fields when the user lacks the permission.

## Customizing

- **Templates** live under `django_utils/`; override them from your own app. Put your app **before** `django_utils`
  in `INSTALLED_APPS`: Django uses the first template found.
- **Hooks**: `ExtraPermissionsBackend.get_extra_permissions()`, `HTMXRenderer.partials_path` /
  `action_suffixes`, `GatedFieldsSerializerMixin.gated_fields`, `StorageSizeMixin.update_size()`,
  `ClassRegistryMixin._registry_key()`.
- **System checks** `django_utils.E001` to `E003` validate the `gated_features` of your models.

## Development

```bash
uv sync --all-extras                                    # create the venv, install dev tools and extras
uv run python -m django test --settings=tests.settings   # run the tests
uv run ruff check . && uv run ruff format .              # lint and format
uv run pre-commit install                                # enable git hooks
uv build                                                 # build sdist and wheel
```

## Conventions

- KISS and DRY; use Django built-ins, avoid premature abstractions.
- Imports at the top of the file, grouped (stdlib, third-party, Django, local), with `__all__`.
- Line length: 120 characters (Ruff).
- Tests use Django's `unittest` (`django.test`), not pytest.

## License

[BSD 2-Clause](LICENSE)
