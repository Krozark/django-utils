import factory
from django.contrib.auth import get_user_model

from tests.models import VersionedItem


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    is_staff = False


class VersionedItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VersionedItem

    name = factory.Sequence(lambda n: f"item{n}")
