import tempfile

SECRET_KEY = "test"  # noqa: S105
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django_filters",
    "rest_framework",
    "django_utils",
    "tests",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "django_utils.api.renderers.StandardJSONRenderer",
        "django_utils.api.renderers.HTMXRenderer",
    ],
    "EXCEPTION_HANDLER": "django_utils.api.handlers.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "django_utils.api.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 2,
}

PRIVATE_STORAGE_ROOT = tempfile.mkdtemp(prefix="django-utils-private-")
PRIVATE_STORAGE_AUTH_FUNCTION = "private_storage.permissions.allow_authenticated"
