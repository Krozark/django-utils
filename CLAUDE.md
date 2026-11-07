# CLAUDE.md

`django-utils` is a reusable Django app (import name `django_utils`, `src/` layout, built with `uv_build`).

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
uv sync
uv run ruff check . && uv run ruff format .
uv build
```
