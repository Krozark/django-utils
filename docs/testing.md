# Testing with `django_utils.testing`: a complete example

This walks through one small app, from the settings to the contract of its viewset. Sections 1 to 5 are adapted from
the test suite of this repository (`tests/models.py` and `tests/testing/`), which runs on every supported Django
version; section 6 is illustrative (`apply_discount` and `OrderFactory` are placeholders).

Install the extras: `django-utils[testing,drf]` (`drf` only for the `django_utils.testing.api` part).

## 1. Settings

Test storages must live in the system temporary directory: `MediaCleanupMixin` empties them and refuses to touch
anything else.

```python
# settings for the tests
import tempfile

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": tempfile.mkdtemp(prefix="myapp-media-")},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
```

## 2. The code under test

```python
# models.py
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class ContractItemQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class ContractItemManager(models.Manager.from_queryset(ContractItemQuerySet)):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class ContractItem(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    objects = ContractItemManager()

    class Meta:
        verbose_name = _("contract item")
        verbose_name_plural = _("contract items")
        constraints = [
            models.CheckConstraint(condition=models.Q(slug__gt=""), name="myapp__contractitem__slug_not_empty"),
        ]

    def __str__(self):
        return self.title

    def natural_key(self):
        return (self.slug,)

    def get_upper_title(self):
        return self.title.upper()

    @property
    def upper_title(self):
        return self.get_upper_title()

    def get_lower_title(self):
        return self.title.lower()

    @cached_property
    def lower_title(self):
        return self.get_lower_title()
```

A custom field with its own lookup:

```python
from django.db.models import Lookup


class TagField(models.CharField):
    """CharField with an extra ``ne`` lookup."""


@TagField.register_lookup
class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} <> {rhs}", [*lhs_params, *rhs_params]


class TaggedItem(models.Model):
    tag = TagField(max_length=20)
```

And the REST layer:

```python
# api.py
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ContractItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractItem
        fields = ["id", "slug", "title", "is_active"]
        read_only_fields = ["id"]


class ContractItemFilterSet(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    title = django_filters.CharFilter(lookup_expr="icontains")
    min_id = django_filters.NumberFilter(field_name="id", lookup_expr="gte")

    class Meta:
        model = ContractItem
        fields = []


class ContractItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff sees every item, everybody else only the active ones."""

    serializer_class = ContractItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ContractItemFilterSet
    lookup_field = "slug"

    def get_queryset(self):
        queryset = ContractItem.objects.order_by("title")
        if self.request.user.is_staff:
            return queryset
        return queryset.active()

    @action(detail=False, methods=["get"], url_path="titles")
    def titles(self, request):
        return Response(list(self.get_queryset().values_list("title", flat=True)))
```

```python
# urls.py
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("items", ContractItemViewSet, basename="contractitem")

urlpatterns = router.urls
```

## 3. Factories

Contracts get their objects from factory-boy factories.

```python
# factories.py
import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    is_staff = False


class ContractItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContractItem

    slug = factory.Sequence(lambda n: f"item-{n}")
    title = factory.Sequence(lambda n: f"Item {n}")


class TaggedItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaggedItem

    tag = factory.Sequence(lambda n: f"tag{n}")
```

## 4. Contracts for models, fields, lookups and managers

You declare everything the class is expected to expose; undeclared fields, properties, filters or actions fail the
test. Every constraint needs a `test_constraint_<name>` method and a name starting with
`<app_label>__<model_name>__`.

```python
from django.db import IntegrityError, models, transaction
from django_utils.testing import (
    FieldContractTestCase,
    LookupContractTestCase,
    ManagerContractTestCase,
    ModelContractTestCase,
)


class ContractItemContract(ModelContractTestCase):
    model = ContractItem
    factory = ContractItemFactory  # builds, without saving, the instance used below
    build_kwargs = {"slug": "abc", "title": "Hello"}

    expected_repr = "<ContractItem: Hello>"
    expected_natural_key = ("abc",)  # None: the model must not define natural_key
    expected_verbose_names = {"en": ("contract item", "contract items")}
    expected_fields = {
        "id": models.BigAutoField,
        "slug": models.SlugField,
        "title": models.CharField,
        "is_active": models.BooleanField,
    }
    expected_properties = {
        "upper_title": {"getter_method": "get_upper_title"},
        "lower_title": {"getter_method": "get_lower_title", "cached": True},
    }

    def test_constraint_myapp__contractitem__slug_not_empty(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ContractItemFactory(slug="")


class TagFieldContract(FieldContractTestCase):
    field_class = TagField
    expected_base_class = models.CharField
    expected_lookups = {**models.CharField.get_lookups(), "ne": NotEqual}
    expected_default_validators = []


class UnprintableValue:
    """A value the field cannot convert to a string, so that the lookup raises."""

    def __str__(self):
        raise TypeError("cannot be converted")


class NotEqualContract(LookupContractTestCase):
    lookup_class = NotEqual
    model = TaggedItem
    lookup_field_name = "tag"
    expected_lookup_name = "ne"
    expected_querysets = [
        {"value": "a", "instances": [1, 2]},  # indexes in self.instances
        {"value": "zzz", "instances": [0, 1, 2]},
        {"value": UnprintableValue(), "raises": TypeError},  # the filter must raise
    ]

    def create_fixtures(self):
        self.instances = [TaggedItemFactory(tag=tag) for tag in ("a", "b", "c")]


class ContractItemManagerContract(ManagerContractTestCase):
    model = ContractItem
    expected_manager_class = ContractItemManager
    expected_natural_keys = [  # None: no get_by_natural_key expected
        {"key": ("does-not-exist",), "instance": None},
        {"key": ("first",), "instance": 0},
        {"key": ("second",), "instance": 1},
    ]
    expected_method_availabilities = {
        "active": {"manager": True, "queryset": True},
        "get_by_natural_key": {"manager": True, "queryset": False},
    }

    def create_fixtures(self):
        self.instances = [ContractItemFactory(slug="first"), ContractItemFactory(slug="second")]
```

`create_fixtures()` is the single hook filling `self.instances`; it runs before each generated test that needs data,
inside that test's transaction.

## 5. Contracts for the REST layer

```python
from rest_framework import serializers
from django_utils.testing.api import FilterSetContractTestCase, SerializerContractTestCase


class ContractItemSerializerContract(SerializerContractTestCase):
    serializer_class = ContractItemSerializer
    users = {"admin": lambda: UserFactory(is_staff=True)}  # callables are resolved once per class

    expected_fields = {  # exact classes
        "id": serializers.BigIntegerField,
        "slug": serializers.SlugField,
        "title": serializers.CharField,
        "is_active": serializers.BooleanField,
    }
    expected_readable_fields = {"id", "slug", "title", "is_active"}
    expected_writable_fields = {"slug", "title", "is_active"}
    expected_required_fields = {"slug", "title"}
    expected_representations = [
        {"instance": 0, "expected": {"id": 1, "slug": "first", "title": "Alpha", "is_active": True}},
        {
            "name": "many as admin",
            "instances": [0, 1],
            "user": "admin",
            "expected": [
                {"id": 1, "slug": "first", "title": "Alpha", "is_active": True},
                {"id": 2, "slug": "second", "title": "Bravo", "is_active": False},
            ],
        },
    ]
    expected_validation_errors = [
        {"data": {"title": "x"}, "errors": {"slug": ["This field is required."]}},
        {"data": {"slug": "second"}, "instance": 1, "partial": True, "errors": {}},
    ]

    def create_fixtures(self):
        self.instances = [
            ContractItemFactory(pk=1, slug="first", title="Alpha"),
            ContractItemFactory(pk=2, slug="second", title="Bravo", is_active=False),
        ]
```

Filters are checked by the contract, and each one needs a `test_filter_<name>` method written with `assert_filter`:

```python
class ContractItemFilterSetContract(FilterSetContractTestCase):
    filterset_class = ContractItemFilterSet

    expected_filters = {
        "is_active": django_filters.BooleanFilter,
        "title": django_filters.CharFilter,
        "min_id": django_filters.NumberFilter,
    }

    def setUp(self):
        self.instances = [
            ContractItemFactory(pk=1, title="Alpha", is_active=True),
            ContractItemFactory(pk=2, title="Bravo", is_active=False),
            ContractItemFactory(pk=3, title="alphabet", is_active=True),
        ]

    def test_filter_is_active(self):
        self.assert_filter("is_active", data={"is_active": "true"}, expected_instances=[0, 2])

    def test_filter_title(self):
        self.assert_filter("title", data={"title": "alpha"}, expected_instances=[0, 2])

    def test_filter_min_id(self):
        self.assert_filter("min_id", data={"min_id": "2"}, expected_instances=[1, 2])
        self.assert_filter(
            "min_id", data={"min_id": "abc"}, expected_instances=[0, 1, 2], expected_errors=["Enter a number."]
        )
```

The viewset is exercised through its real URLs, so the test needs a `ROOT_URLCONF` routing it:

```python
from django.test import override_settings
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from django_utils.api.pagination import StandardResultsSetPagination
from django_utils.api.renderers import HTMXRenderer, StandardJSONRenderer
from django_utils.testing.api import ViewSetContractTestCase


@override_settings(ROOT_URLCONF="myapp.urls")
class ContractItemViewSetContract(ViewSetContractTestCase):
    viewset_class = ContractItemViewSet
    url_basename = "contractitem"
    action_url_kwargs = {"retrieve": {"slug": "first"}}
    users = {
        "anonymous": None,
        "user": lambda: UserFactory(username="user"),
        "admin": lambda: UserFactory(username="admin", is_staff=True),
    }

    expected_lookup_field = "slug"
    expected_actions = ["list", "retrieve", "titles"]
    expected_filter_backends = [DjangoFilterBackend]
    expected_filterset_classes = {
        "list": ContractItemFilterSet,
        "retrieve": ContractItemFilterSet,
        "titles": ContractItemFilterSet,
    }
    expected_serializer_classes = {"list": ContractItemSerializer, "retrieve": ContractItemSerializer}
    expected_pagination_class = StandardResultsSetPagination
    expected_renderer_classes = [StandardJSONRenderer, HTMXRenderer]
    expected_parser_classes = [JSONParser, FormParser, MultiPartParser]

    expected_permissions = [
        {"action": action, "user": user, "allowed": user != "anonymous"}
        for action in ("list", "retrieve", "titles")
        for user in ("anonymous", "user", "admin")
    ]
    expected_querysets = [
        {"user": "anonymous", "instances": [0, 1]},
        {"user": "user", "instances": [0, 1]},
        {"user": "admin", "instances": [0, 1, 2]},
    ]
    expected_orderings = [{"user": "admin", "instances": [0, 1, 2]}]
    expected_query_counts = [
        {"action": "list", "user": "admin", "count": 2},
        {"action": "retrieve", "user": "user", "count": 1},
        {"action": "titles", "user": "admin", "count": 1},
    ]

    def create_fixtures(self):
        self.instances = [
            ContractItemFactory(pk=1, slug="first", title="Alpha"),
            ContractItemFactory(pk=2, slug="second", title="Bravo"),
            ContractItemFactory(pk=3, slug="hidden", title="Charlie", is_active=False),
        ]
```

`strict_coverage` (on by default) makes this contract fail if an action x user permission, an action filterset, a
user queryset or the query count of a safe action is missing. Set `strict_coverage = False` to opt out.

## 6. Helpers for your own tests

```python
from django_utils.testing import TestCase, subtests_cases, with_fixtures


class PricingTests(TestCase):
    frozen_time = "2012-01-14 03:21:34"  # needs the testing extra (freezegun)

    @subtests_cases(
        {
            "valid": [5, 10],  # data passed as the second argument
            "negative": {"data": [-1, 10], "raises": ValueError, "message": "negative"},
        }
    )
    def test_discount(self, data):  # each case: sub-test + rolled-back transaction
        amount, total = data
        apply_discount(amount, total)

    def fixtures_total(self):  # called before test_total
        self.order = OrderFactory()

    @with_fixtures()
    def test_total(self):
        self.assertEqual(self.order.total, 12)
```

## 7. Running

Contracts are ordinary `unittest` classes: `python manage.py test`. Base classes imported in a test module are skipped
by themselves; a subclass forgetting a required attribute (`model`, `viewset_class`...) raises an error naming it.
