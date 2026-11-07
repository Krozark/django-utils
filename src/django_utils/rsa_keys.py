"""RSA key-pair loader, shared by every subsystem that needs a stable key pair (token signing, ...).

Needs the ``crypto`` extra (``cryptography`` and ``django-environ``).

Isolated from the settings module so that it stays declarative:

- **Always** reads PEM content from a pair of env vars chosen by the caller.
- In **development**, call :func:`ensure_dev_keys` once (at the top of
  the development settings) to auto-generate and persist any missing pairs into
  ``.env`` before the rest of the settings load.  Pass ``export_dir`` to also
  write ``.pem`` files for clients that read keys from disk.
"""

import logging
import os
import tempfile
from pathlib import Path

import environ
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ImproperlyConfigured

__all__ = [
    "ensure_dev_keys",
    "load_rsa_key_pair",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_rsa_key_pair() -> tuple[bytes, bytes]:
    """Generate a fresh RSA-2048 key pair; return ``(private_pem, public_pem)``."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _export_key_files(export_dir: Path, key_name: str, private_pem: bytes, public_pem: bytes) -> None:
    """Write ``<key_name>_private.pem`` and ``<key_name>_public.pem`` to ``export_dir``."""
    export_dir.mkdir(parents=True, exist_ok=True)
    private_path = export_dir / f"{key_name}_private.pem"
    public_path = export_dir / f"{key_name}_public.pem"
    fd, tmp = tempfile.mkstemp(dir=export_dir)
    try:
        os.write(fd, private_pem)
    finally:
        os.close(fd)
    Path(tmp).rename(private_path)
    public_path.write_bytes(public_pem)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def ensure_dev_keys(
    env_path: Path,
    *key_specs: tuple[str, str, str],
    export_dir: Path | None = None,
) -> None:
    """Ensure each ``(PRIVATE_VAR, PUBLIC_VAR, key_name)`` pair exists in ``os.environ``.

    Designed to be called **once**, at the very top of the development settings,
    before ``from .base import *``.  Resolution order for each pair:

    1. Already in ``os.environ`` (e.g. exported in the shell) → keep as-is.
    2. Present in ``env_path`` (.env file) → load it into ``os.environ``.
    3. Missing everywhere → generate a fresh RSA-2048 pair, append it to
       ``env_path`` as a single-line ``\\n``-escaped entry, and set it in
       ``os.environ`` so the value is immediately available.

    If ``export_dir`` is given, the current key pair (whether loaded or freshly
    generated) is also written as ``<key_name>_{private,public}.pem`` under
    that directory on every startup.  Useful for client apps that
    read keys from disk rather than from env vars.

    **Never call this in production.**
    """
    if Path(env_path).exists():
        environ.Env.read_env(str(env_path), overwrite=False)

    to_generate = [spec for spec in key_specs if not (os.environ.get(spec[0]) and os.environ.get(spec[1]))]

    if to_generate:
        with open(env_path, "a") as f:
            for priv_var, pub_var, _key_name in to_generate:
                private_pem, public_pem = _generate_rsa_key_pair()
                private_line = private_pem.decode().replace("\n", "\\n")
                public_line = public_pem.decode().replace("\n", "\\n")
                os.environ[priv_var] = private_line
                os.environ[pub_var] = public_line
                f.write(f'\n{priv_var}="{private_line}"\n')
                f.write(f'{pub_var}="{public_line}"\n')
                logger.warning(
                    "Dev: generated RSA key pair for %s / %s and appended it to %s. "
                    "Do NOT use these keys in production.",
                    priv_var,
                    pub_var,
                    env_path,
                )

    if export_dir is not None:
        for priv_var, pub_var, key_name in key_specs:
            private_pem = os.environ[priv_var].replace("\\n", "\n").encode()
            public_pem = os.environ[pub_var].replace("\\n", "\n").encode()
            _export_key_files(export_dir, key_name, private_pem, public_pem)


def load_rsa_key_pair(
    *,
    env_private_var: str,
    env_public_var: str,
) -> tuple[bytes, bytes]:
    """Return ``(private_pem, public_pem)`` bytes read from environment variables.

    Env vars may store PEM newlines as the two-character sequence ``\\n``
    (standard for single-line ``.env`` entries, Docker env files, systemd
    ``EnvironmentFile``).  Those are unescaped before returning so callers
    always receive real PEM bytes.

    Raises :exc:`django.core.exceptions.ImproperlyConfigured` if either
    variable is absent or empty.
    """
    private = os.environ.get(env_private_var)
    public = os.environ.get(env_public_var)
    if private and public:
        return private.replace("\\n", "\n").encode(), public.replace("\\n", "\n").encode()
    missing = [var for var, val in ((env_private_var, private), (env_public_var, public)) if not val]
    raise ImproperlyConfigured(f"Missing environment variable(s): {', '.join(missing)}")
