import factory
from django.conf import settings
from factory.django import DjangoModelFactory

__all__ = ["CreatedByMixinFactory", "IsPublicMixinFactory", "UserFactory"]


class UserFactory(DjangoModelFactory):
    """Users of ``AUTH_USER_MODEL``, with a unique username and an email derived from it.

    Subclass it to add what a custom user model needs (extra required fields, a password, a profile...).
    """

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_active = True
    is_staff = False
    is_superuser = False


class IsPublicMixinFactory(DjangoModelFactory):
    """Base factory of the models using ``IsPublicMixin``: ``is_public`` is random, pass it to force a value."""

    class Meta:
        abstract = True

    is_public = factory.Faker("boolean")


class CreatedByMixinFactory(DjangoModelFactory):
    """Base factory of the models using ``CreatedByMixin``: each object gets its own user.

    Override ``created_by`` with a ``SubFactory`` of your own user factory when ``UserFactory`` does not fit. Combine
    it with ``IsPublicMixinFactory`` for the models that also use ``IsPublicMixin``.
    """

    class Meta:
        abstract = True

    created_by = factory.SubFactory(UserFactory)
