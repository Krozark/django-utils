"""Tests for django_utils.rsa_keys."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase

from django_utils import rsa_keys

__all__ = [
    "LoadRsaKeyPairTests",
    "EnsureDevKeysTests",
]

_ENV_PRIVATE_VAR = "TEST_KEY_PRIVATE"
_ENV_PUBLIC_VAR = "TEST_KEY_PUBLIC"
_KEY_SPEC = (_ENV_PRIVATE_VAR, _ENV_PUBLIC_VAR, "test_key")


class LoadRsaKeyPairTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for var in (_ENV_PRIVATE_VAR, _ENV_PUBLIC_VAR):
            os.environ.pop(var, None)
        self.addCleanup(self._env_patch.stop)

    def _load(self):
        return rsa_keys.load_rsa_key_pair(
            env_private_var=_ENV_PRIVATE_VAR,
            env_public_var=_ENV_PUBLIC_VAR,
        )

    def test_returns_bytes_from_env_vars(self):
        os.environ[_ENV_PRIVATE_VAR] = "PRIV"
        os.environ[_ENV_PUBLIC_VAR] = "PUB"

        private, public = self._load()

        self.assertEqual(private, b"PRIV")
        self.assertEqual(public, b"PUB")

    def test_unescapes_newlines(self):
        os.environ[_ENV_PRIVATE_VAR] = "-----BEGIN PRIVATE KEY-----\\nABC\\n-----END PRIVATE KEY-----"
        os.environ[_ENV_PUBLIC_VAR] = "-----BEGIN PUBLIC KEY-----\\nDEF\\n-----END PUBLIC KEY-----"

        private, public = self._load()

        self.assertIn(b"\n", private)
        self.assertIn(b"\n", public)
        self.assertEqual(private, b"-----BEGIN PRIVATE KEY-----\nABC\n-----END PRIVATE KEY-----")

    def test_raises_when_private_key_missing(self):
        os.environ[_ENV_PUBLIC_VAR] = "PUB"

        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._load()

        self.assertIn(_ENV_PRIVATE_VAR, str(ctx.exception))

    def test_raises_when_public_key_missing(self):
        os.environ[_ENV_PRIVATE_VAR] = "PRIV"

        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._load()

        self.assertIn(_ENV_PUBLIC_VAR, str(ctx.exception))

    def test_raises_when_both_missing(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._load()

        self.assertIn(_ENV_PRIVATE_VAR, str(ctx.exception))
        self.assertIn(_ENV_PUBLIC_VAR, str(ctx.exception))


class EnsureDevKeysTests(TestCase):
    def setUp(self):
        super().setUp()
        self._env_patch = mock.patch.dict(os.environ, {}, clear=False)
        self._env_patch.start()
        for var in (_ENV_PRIVATE_VAR, _ENV_PUBLIC_VAR):
            os.environ.pop(var, None)
        self.addCleanup(self._env_patch.stop)

    def test_generates_keys_and_sets_env_vars_when_absent(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)

        self.assertIn(_ENV_PRIVATE_VAR, os.environ)
        self.assertIn(_ENV_PUBLIC_VAR, os.environ)

    def test_generated_key_is_valid_pem(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)

        priv_bytes = os.environ[_ENV_PRIVATE_VAR].replace("\\n", "\n").encode()
        pub_bytes = os.environ[_ENV_PUBLIC_VAR].replace("\\n", "\n").encode()
        load_pem_private_key(priv_bytes, password=None)
        load_pem_public_key(pub_bytes)

    def test_appends_to_env_file(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("EXISTING=value\n")

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)

            content = env_path.read_text()

        self.assertIn("EXISTING=value", content)
        self.assertIn(_ENV_PRIVATE_VAR, content)
        self.assertIn(_ENV_PUBLIC_VAR, content)

    def test_keys_in_env_file_are_single_line(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)

            for line in env_path.read_text().splitlines():
                if _ENV_PRIVATE_VAR in line or _ENV_PUBLIC_VAR in line:
                    self.assertIn("\\n", line, "PEM must be stored as \\n-escaped single line")

    def test_skips_generation_when_env_vars_already_set(self):
        os.environ[_ENV_PRIVATE_VAR] = "existing_priv"
        os.environ[_ENV_PUBLIC_VAR] = "existing_pub"

        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()

            with mock.patch.object(rsa_keys, "_generate_rsa_key_pair") as gen:
                rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)

            gen.assert_not_called()

        self.assertEqual(os.environ[_ENV_PRIVATE_VAR], "existing_priv")

    def test_loads_existing_env_file_before_generating(self):
        """Keys already in .env must not trigger a second generation."""
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()
            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)
            first_priv = os.environ[_ENV_PRIVATE_VAR]

            os.environ.pop(_ENV_PRIVATE_VAR)
            os.environ.pop(_ENV_PUBLIC_VAR)
            with mock.patch.object(rsa_keys, "_generate_rsa_key_pair") as gen:
                rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC)
                gen.assert_not_called()

        self.assertEqual(os.environ[_ENV_PRIVATE_VAR], first_priv)

    def test_two_key_pairs_are_independent(self):
        priv2, pub2 = "TEST_KEY2_PRIVATE", "TEST_KEY2_PUBLIC"
        for var in (priv2, pub2):
            os.environ.pop(var, None)

        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC, (priv2, pub2, "test_key2"))

        self.assertNotEqual(os.environ[_ENV_PRIVATE_VAR], os.environ[priv2])
        for var in (priv2, pub2):
            os.environ.pop(var, None)

    def test_export_dir_writes_pem_files(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            export_dir = Path(tmp) / "keys"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC, export_dir=export_dir)

            self.assertTrue((export_dir / "test_key_private.pem").exists())
            self.assertTrue((export_dir / "test_key_public.pem").exists())

    def test_export_dir_files_contain_valid_pem(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            export_dir = Path(tmp) / "keys"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC, export_dir=export_dir)

            priv_bytes = (export_dir / "test_key_private.pem").read_bytes()
            pub_bytes = (export_dir / "test_key_public.pem").read_bytes()

        load_pem_private_key(priv_bytes, password=None)
        load_pem_public_key(pub_bytes)

    def test_export_dir_private_file_is_owner_readable_only(self):
        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            export_dir = Path(tmp) / "keys"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC, export_dir=export_dir)

            mode = (export_dir / "test_key_private.pem").stat().st_mode & 0o777

        self.assertEqual(mode, 0o600)

    def test_export_dir_refreshed_on_every_call(self):
        """Even when env vars are already set, export_dir is always written."""
        os.environ[_ENV_PRIVATE_VAR] = "-----BEGIN PRIVATE KEY-----\\nABC\\n-----END PRIVATE KEY-----"
        os.environ[_ENV_PUBLIC_VAR] = "-----BEGIN PUBLIC KEY-----\\nDEF\\n-----END PUBLIC KEY-----"

        with TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            export_dir = Path(tmp) / "keys"
            env_path.touch()

            rsa_keys.ensure_dev_keys(env_path, _KEY_SPEC, export_dir=export_dir)

            self.assertTrue((export_dir / "test_key_private.pem").exists())
            self.assertTrue((export_dir / "test_key_public.pem").exists())
