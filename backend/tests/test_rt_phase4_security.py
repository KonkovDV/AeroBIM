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


class PathJailAdversarialProbeTests(unittest.TestCase):
    """Permanent home of the adversarial probe corpus (ex backend/_probe_jail.py).

    Each vector was fired against ``resolve_storage_path`` on 2026-07-26;
    traversal-class inputs were already rejected, the Windows-specific class
    (ADS colons, reserved device names, overlong components, trailing dots)
    was ACCEPTED and is now closed by ``_validate_path_components``.
    """

    REJECTED_VECTORS = (
        "evil.png::$DATA",  # NTFS alternate data stream
        "a/evil.txt:hidden",  # named ADS in nested component
        "CON",  # reserved device name, bare
        "NUL.txt",  # reserved device name survives an extension
        "aux.tar.gz",  # reserved name, case-insensitive, multi-suffix
        "COM1",
        "x" * 300 + ".png",  # component beyond the NTFS 255-char limit
        "trailing./x",  # Windows strips trailing dots -> collision
        "trailing /x",  # Windows strips trailing spaces -> collision
        "...",  # trailing-dot component (Windows strips to '..'-lookalike)
        "\u2025\u2025/x",  # two-dot leader: NFKC -> '....' -> trailing-dot reject
        "\uff0e\uff0e/\uff0e\uff0e/etc",  # fullwidth dots -> NFKC '..'
        "%2e%2e/%2e%2e/secret",  # percent-encoded traversal
        " ..%2fsecret",  # leading space + encoded slash
    )

    ACCEPTED_VECTORS = (
        "%252e%252e/x",  # double encoding decodes once to literal '%2e%2e' (no traversal)
        "a\u2215b",  # division slash is NOT NFKC-normalized to '/' -> plain filename
        "..\u2044etc",  # fraction slash is NOT NFKC-normalized -> plain filename
        "console.log",  # 'CON' must match whole stem only, not a prefix
        "a/./b",  # single-dot components collapse harmlessly
    )

    def test_adversarial_vectors_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            for vector in self.REJECTED_VECTORS:
                with self.subTest(vector=ascii(vector)):
                    with self.assertRaises(PathJailError):
                        resolve_storage_path(vector, base=base)

    def test_benign_lookalikes_stay_inside_jail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            for vector in self.ACCEPTED_VECTORS:
                with self.subTest(vector=ascii(vector)):
                    resolved = resolve_storage_path(vector, base=base)
                    self.assertTrue(resolved.is_relative_to(base.resolve()))

    def test_traversal_via_dot_dot_still_names_boundary(self) -> None:
        # The '..' layer must keep its specific message so component checks
        # (which skip '..') never shadow the boundary rejection.
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            with self.assertRaisesRegex(PathJailError, "escapes storage boundary"):
                resolve_storage_path("../outside.ifc", base=base)

    def test_component_length_boundary_255_256(self) -> None:
        # Mutation-strength boundary: `> 255` mutants (>=, >256) disagree here.
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            ok = resolve_storage_path("x" * 255, base=base)
            self.assertEqual(len(ok.name), 255)
            with self.assertRaisesRegex(PathJailError, "maximum length"):
                resolve_storage_path("x" * 256, base=base)

    def test_reserved_name_matches_stem_not_substring(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            # Whole-stem matches rejected regardless of case / extension depth.
            for bad in ("nul", "Con.ifc", "lpt9.a.b"):
                with self.subTest(vector=bad):
                    with self.assertRaisesRegex(PathJailError, "reserved device name"):
                        resolve_storage_path(bad, base=base)
            # Prefix / suffix lookalikes stay valid filenames.
            for good in ("nullable.ifc", "falcon.ifc", "COM10"):
                with self.subTest(vector=good):
                    resolved = resolve_storage_path(good, base=base)
                    self.assertTrue(resolved.is_relative_to(base.resolve()))


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
