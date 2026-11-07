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
