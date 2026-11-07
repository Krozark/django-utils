__all__ = [
    "ClassRegistryMixin",
]


class ClassRegistryMixin:
    """Self-registers every concrete subclass into a dict keyed by `_registry_key()`.

    Factors out the `__init_subclass__` self-registration pattern: every concrete
    subclass (as opposed to an abstract intermediate) adds itself to a registry,
    so a dispatcher can later resolve `some_string -> the right subclass` without
    a hand-written if/elif chain.

    Deliberately provides NO default registry here. Each abstract root that uses
    this mixin MUST declare its own registry dict and override `get_registry()`
    to return it — a single dict defined on the mixin itself would be shared by
    every hierarchy that inherits it, silently merging unrelated registries.
    Leaving `get_registry()` unimplemented here means a root that forgets to
    override it fails loudly (`NotImplementedError`) the moment its first
    concrete subclass is defined, instead of silently sharing another
    hierarchy's dict.

    Usage::

        class Shape(ClassRegistryMixin, models.Model):
            _class_registry: dict = {}

            class Meta:
                abstract = True

            @classmethod
            def get_registry(cls) -> dict:
                return cls._class_registry

            @classmethod
            def _registry_key(cls) -> str:
                return cls.__name__
    """

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls._meta.abstract:
            cls.get_registry()[cls._registry_key()] = cls

    @classmethod
    def get_registry(cls) -> dict:
        """Return THIS hierarchy's registry dict. Must be overridden by the abstract root."""
        raise NotImplementedError

    @classmethod
    def _registry_key(cls) -> str:
        """Return the key this concrete subclass registers itself under. Must be overridden."""
        raise NotImplementedError
