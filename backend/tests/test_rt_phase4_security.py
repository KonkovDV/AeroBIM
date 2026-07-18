"""Phase 4 security: path jail fuzz + no production S3→FS fallback."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.core.security.path_jail import PathJailError, resolve_storage_path
from aerobim.infrastructure.di import bootstrap as bootstrap_module


class PathJailFuzzTests(unittest.TestCase):
    def test_rejects_null_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaises(PathJailError):
                resolve_storage_path("uploads/\x00evil.ifc", base=base)

    def test_rejects_percent_encoded_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaises(PathJailError):
                resolve_storage_path("%2e%2e/outside.ifc", base=base)
            with self.assertRaises(PathJailError):
                resolve_storage_path("..%2foutside.ifc", base=base)

    def test_rejects_unc_and_drive_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaises(PathJailError):
                resolve_storage_path(r"\\server\share\file.ifc", base=base)
            with self.assertRaises(PathJailError):
                resolve_storage_path(r"C:\Windows\system32\config", base=base)

    def test_rejects_control_characters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaises(PathJailError):
                resolve_storage_path("uploads/evil\n.ifc", base=base)


class ObjectStoreFallbackTests(unittest.TestCase):
    def test_pilot_profile_does_not_fallback_to_filesystem(self) -> None:
        settings = Settings(
            application_name="aerobim",
            environment="development",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=True,
            s3_bucket="aerobim-pilot",
            signoff_profile="samolet_pilot",
        )
        with patch.object(
            bootstrap_module,
            "S3ObjectStore",
            side_effect=RuntimeError("boto3 missing"),
        ):
            with self.assertRaises(RuntimeError):
                bootstrap_module._build_object_store(settings)

    def test_dev_profile_may_fallback_to_filesystem(self) -> None:
        settings = Settings(
            application_name="aerobim",
            environment="development",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=True,
            s3_bucket="aerobim-dev",
            signoff_profile="development",
        )
        with patch.object(
            bootstrap_module,
            "S3ObjectStore",
            side_effect=RuntimeError("boto3 missing"),
        ):
            store = bootstrap_module._build_object_store(settings)
            self.assertEqual(type(store).__name__, "LocalObjectStore")


if __name__ == "__main__":
    unittest.main()
