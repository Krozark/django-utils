import hashlib

from django.contrib.auth import get_permission_codename

__all__ = [
    "M2M_APPEND",
    "M2M_REPLACE",
    "get_model_permission",
    "lookup_by_uuid",
    "md5_checksum",
    "set_m2m",
]

M2M_APPEND = "append"
M2M_REPLACE = "replace"


def md5_checksum(file_obj):
    """Compute MD5 hex digest of a file-like object.

    Reads in 8 KB chunks and resets the seek position before and after.
    Returns the 32-character hex digest string.
    """
    file_obj.seek(0)
    md5 = hashlib.md5(usedforsecurity=False)
    for chunk in iter(lambda: file_obj.read(8192), b""):
        md5.update(chunk)
    file_obj.seek(0)
    return md5.hexdigest()


def set_m2m(instance, field_name, objects, m2m_mode=M2M_APPEND):
    """Set M2M relation using append or replace mode."""
    manager = getattr(instance, field_name)
    if m2m_mode == M2M_REPLACE:
        manager.set(objects)
    else:
        manager.add(*objects)


def lookup_by_uuid(model_class, uuid_str, user):
    """Look up a model instance by UUID for a specific user.

    The model must have ``uuid`` and ``created_by`` fields (see ``UUIDMixin`` and ``CreatedByMixin``).

    Returns (instance, can_reuse_uuid) where:
    - instance is the existing object if found for this user, else None
    - can_reuse_uuid is True if the UUID can be used for a new object
    """
    try:
        return model_class.objects.get(uuid=uuid_str, created_by=user), True
    except model_class.DoesNotExist:
        uuid_taken = model_class.objects.filter(uuid=uuid_str).exists()
        return None, not uuid_taken


def get_model_permission(model, action):
    """Return the ``'<app_label>.<action>_<model_name>'`` permission string of a model.

    Example: ``get_model_permission(Ambience, "add") -> "nara_ava.add_ambience"``
    """
    opts = model._meta
    return f"{opts.app_label}.{get_permission_codename(action, opts)}"
