# django-utils

Reusable Django utilities (models, mixins, helpers) shared across projects.

## Installation

```bash
uv add "django-utils @ git+https://github.com/Krozark/django-utils.git"
```

Then add it to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "django_utils",
]
```

Compatible with Django 5.0+ and 6.x, Python 3.12+.

## Model mixins

`django_utils.models` provides abstract models and helpers:

| Name | Purpose |
|---|---|
| `UUIDMixin` | `uuid` field (not the primary key) |
| `CreatedByMixin` | `created_by` FK to the user model + `created_at` / `updated_at` |
| `IsPublicMixin` | `is_public` flag + `manager_public` manager |
| `VersionFieldMixin` / `AutoVersionFieldMixin` | `version` counter, auto-incremented when a field changes |
| `StorageSizeMixin` | `storage_size` in bytes, refreshed on each save through `update_size()` |
| `SoftDeletionMixin` | soft delete with a grace period |
| `ClassRegistryMixin` | self-registration of concrete subclasses |

## Admin, forms and helpers

- `django_utils.admin`: `CreatedByAdminMixin` (users only see and edit their own objects, with a username filter),
  `IsPublicAdminMixin`, `ReadOnlyAdminMixin`. The username filter uses a template shipped with the app, so
  `django_utils` must be in `INSTALLED_APPS`.
- `django_utils.forms.FileSizeField`: accepts `100MB`, `1 GB`... and cleans to bytes.
- `django_utils.utils`: `md5_checksum`, `set_m2m`, `lookup_by_uuid`, `get_model_permission`.

## Development

```bash
uv sync                                                  # create the venv and install dev tools
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
