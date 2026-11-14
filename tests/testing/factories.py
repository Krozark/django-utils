import factory
from django.contrib.auth import get_user_model

from tests.models import ContractItem, TaggedItem, VersionedItem


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


class ContractItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContractItem

    slug = factory.Sequence(lambda n: f"item-{n}")
    title = factory.Sequence(lambda n: f"Item {n}")


class TaggedItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaggedItem

    tag = factory.Sequence(lambda n: f"tag{n}")
