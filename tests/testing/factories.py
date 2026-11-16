import factory
from django.contrib.auth import get_user_model

from django_utils.testing.factories import UserFactory as BaseUserFactory
from tests.models import ContractItem, TaggedItem, VersionedItem


class UserFactory(BaseUserFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ("username",)


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
