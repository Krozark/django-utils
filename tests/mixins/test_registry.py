from django.test import SimpleTestCase

from django_utils.models import ClassRegistryMixin


class _FakeMeta:
    def __init__(self, abstract):
        self.abstract = abstract


def _make_root():
    """A minimal, correctly-configured ClassRegistryMixin root."""

    class Root(ClassRegistryMixin):
        _meta = _FakeMeta(abstract=True)
        _registry = {}

        @classmethod
        def get_registry(cls):
            return cls._registry

        @classmethod
        def _registry_key(cls):
            return cls.__name__

    return Root


class ClassRegistryMixinTests(SimpleTestCase):
    """Plain fake ``_meta`` stand-ins are used: the mixin only ever reads ``cls._meta.abstract``."""

    def test_concrete_subclass_self_registers(self):
        Root = _make_root()

        class Concrete(Root):
            _meta = _FakeMeta(abstract=False)

        self.assertEqual(Root._registry, {"Concrete": Concrete})

    def test_abstract_subclass_does_not_register(self):
        Root = _make_root()

        class StillAbstract(Root):
            _meta = _FakeMeta(abstract=True)

        self.assertEqual(Root._registry, {})

    def test_two_hierarchies_do_not_share_a_registry(self):
        RootA = _make_root()
        RootB = _make_root()

        class ConcreteA(RootA):
            _meta = _FakeMeta(abstract=False)

        class ConcreteB(RootB):
            _meta = _FakeMeta(abstract=False)

        self.assertEqual(RootA._registry, {"ConcreteA": ConcreteA})
        self.assertEqual(RootB._registry, {"ConcreteB": ConcreteB})

    def test_missing_get_registry_override_raises_immediately(self):
        class IncompleteRoot(ClassRegistryMixin):
            _meta = _FakeMeta(abstract=True)

        with self.assertRaises(NotImplementedError):

            class Concrete(IncompleteRoot):
                _meta = _FakeMeta(abstract=False)
