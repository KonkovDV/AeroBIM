"""Negative tests for the decompression/XML bomb guards (RT §8 / §20.15).

These exercise the fail-closed branches of ``core.security.zip_limits`` and
``core.security.xml_limits`` directly (a malicious archive/XML must raise, never
return a partial result). They complement the wiring in bcf_consumers / uploads /
xml_ids_document_auditor. Scope: unit-level guard behaviour, not pilot quality.
"""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from aerobim.core.security.xml_limits import XmlBombError, safe_fromstring
from aerobim.core.security.zip_limits import (
    ZipBombError,
    ZipInspection,
    inspect_zip_bytes,
    inspect_zip_path,
)


def _zip_bytes(members: dict[str, bytes], *, compression: int = zipfile.ZIP_STORED) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=compression) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buf.getvalue()


class ZipBombGuardTests(unittest.TestCase):
    def test_valid_small_zip_inspects_ok(self) -> None:
        result = inspect_zip_bytes(_zip_bytes({"a.txt": b"hello", "b.txt": b"world"}))
        self.assertIsInstance(result, ZipInspection)
        self.assertEqual(result.member_count, 2)

    def test_too_many_members_rejected(self) -> None:
        payload = _zip_bytes({f"m{i}.txt": b"x" for i in range(4)})
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(payload, max_members=2)

    def test_total_uncompressed_cap_rejected(self) -> None:
        payload = _zip_bytes({"a.bin": b"x" * 40, "b.bin": b"y" * 40})
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(payload, max_uncompressed_bytes=10)

    def test_member_too_large_rejected(self) -> None:
        payload = _zip_bytes({"big.bin": b"z" * 100})
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(payload, max_member_bytes=10)

    def test_high_compression_ratio_rejected(self) -> None:
        # A >1 MiB member of zeros compresses to almost nothing -> ratio far > 100.
        payload = _zip_bytes(
            {"bomb.bin": b"\x00" * (2 * 1024 * 1024)}, compression=zipfile.ZIP_DEFLATED
        )
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(payload)

    def test_path_traversal_member_rejected(self) -> None:
        for bad in ("../evil.txt", "/etc/passwd", "sub/../../escape.txt"):
            with self.assertRaises(ZipBombError, msg=bad):
                inspect_zip_bytes(_zip_bytes({bad: b"x"}))

    def test_archive_file_size_cap_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.zip"
            path.write_bytes(_zip_bytes({"a.txt": b"hello"}))
            with self.assertRaises(ZipBombError):
                inspect_zip_path(path, max_archive_file_bytes=1)

    def test_invalid_archive_rejected(self) -> None:
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(b"not-a-zip")


class XmlBombGuardTests(unittest.TestCase):
    def test_valid_small_xml_parses(self) -> None:
        root = safe_fromstring("<root><child/></root>")
        self.assertEqual(root.tag, "root")

    def test_billion_laughs_internal_entity_rejected(self) -> None:
        payload = (
            '<?xml version="1.0"?>'
            "<!DOCTYPE lolz ["
            ' <!ENTITY lol "lol">'
            ' <!ENTITY lol2 "&lol;&lol;">'
            "]>"
            "<lolz>&lol2;</lolz>"
        )
        with self.assertRaises(XmlBombError):
            safe_fromstring(payload)

    def test_external_entity_xxe_rejected(self) -> None:
        payload = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            "<foo>&xxe;</foo>"
        )
        with self.assertRaises(XmlBombError):
            safe_fromstring(payload)

    def test_oversize_payload_rejected(self) -> None:
        with self.assertRaises(XmlBombError):
            safe_fromstring(b"<a/>", max_bytes=1)

    def test_element_count_cap_rejected(self) -> None:
        with self.assertRaises(XmlBombError):
            safe_fromstring("<a><b/><c/></a>", max_elements=1)

    def test_nesting_depth_cap_rejected(self) -> None:
        nested = "<a>" * 8 + "</a>" * 8
        with self.assertRaises(XmlBombError):
            safe_fromstring(nested, max_depth=3)

    def test_text_node_cap_rejected(self) -> None:
        with self.assertRaises(XmlBombError):
            safe_fromstring(f"<a>{'x' * 50}</a>", max_text_chars=10)

    def test_nul_zip_member_rejected(self) -> None:
        from aerobim.core.security.zip_limits import _inspect_zipfile

        class _Info:
            filename = "evil\x00.txt"
            file_size = 1
            compress_size = 1

            def is_dir(self) -> bool:
                return False

        class _Archive:
            def infolist(self) -> list[object]:
                return [_Info()]

        with self.assertRaises(ZipBombError):
            _inspect_zipfile(_Archive())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
