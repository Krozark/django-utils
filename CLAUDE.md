# CLAUDE.md

`django-utils` is a reusable Django app (import name `django_utils`, `src/` layout, built with `uv_build`),
supporting Django 5.0 to 6.x and Python 3.12+. See `README.md` for the module overview.

## Design rules

- **Project-agnostic**: no reference to any project, domain or product. Specific behaviour is a hook (method to
  override, overridable template under `django_utils/`), never an import of the project.
- **Optional dependencies go in extras** (`drf` for `django_utils.api`); the core imports only Django and
  `django-dirtyfields`. Nothing in the core may import `django_utils.api`.
- **Models are abstract** (mixins, `AbstractSubscriptionPlan`): the lib has no migration and no table.
- Reverse names of fields in abstract models use `%(app_label)s_%(class)s_...` so that several models can coexist.
- Tests mirror the package layout (`tests/api`, `tests/gating`, ...) and use the test app models in `tests/models.py`.

## Code Style

- KISS and DRY — use Django built-ins, avoid premature abstractions
- Imports: top of file only, grouped (stdlib → third-party → Django → local), use `__all__`
- Naming: `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE_CASE` constants, `_prefix` private
- Line length: 120 chars max (Ruff enforced)
- Translations: `gettext_lazy` at class level, `gettext` in methods; never f-strings with lazy translation

## Testing

- Django `unittest` only — **not pytest**; tests live in `tests/`

```bash
uv run python -m django test --settings=tests.settings
```

## Commands

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format .
uv build
```

Check a change against the supported Django versions with `uv pip install "django~=5.0.0"` (then `5.2`, `6.1`)
and `uv run --no-sync python -m django test --settings=tests.settings`, then `uv sync --all-extras` to restore.
