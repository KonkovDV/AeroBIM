"""Upload magic-byte validation and size limits (RT-HYPER upload P0)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.security.upload_content import (
    UploadContentError,
    sniff_content,
    validate_upload_content,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class UploadContentSniffTests(unittest.TestCase):
    def test_sniff_pdf_png_jpeg_ifc(self) -> None:
        self.assertEqual(sniff_content(b"%PDF-1.7\n").kind, "pdf")
        self.assertEqual(sniff_content(b"\x89PNG\r\n\x1a\nxxxx").kind, "png")
        self.assertEqual(sniff_content(b"\xff\xd8\xff\xe0").kind, "jpeg")
        self.assertEqual(sniff_content(b"ISO-10303-21;\nDATA;\n").kind, "ifc")

    def test_extension_magic_mismatch_rejected(self) -> None:
        with self.assertRaises(UploadContentError):
            validate_upload_content(filename="model.ifc", payload=b"%PDF-1.7 fake")
        with self.assertRaises(UploadContentError):
            validate_upload_content(filename="sheet.pdf", payload=b"\x89PNG\r\n\x1a\n")

    def test_matching_ifc_and_pdf_accepted(self) -> None:
        ifc = validate_upload_content(filename="model.ifc", payload=b"ISO-10303-21;\n")
        self.assertEqual(ifc.kind, "ifc")
        pdf = validate_upload_content(filename="a.pdf", payload=b"%PDF-1.4\n%")
        self.assertEqual(pdf.kind, "pdf")

    def test_disallowed_extension_rejected(self) -> None:
        with self.assertRaises(UploadContentError):
            validate_upload_content(filename="evil.exe", payload=b"MZ\x90\x00")


class UploadApiSecurityTests(unittest.TestCase):
    def test_upload_rejects_content_mismatch_with_415(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", b"%PDF-1.7\n", "application/pdf")},
            )
            self.assertEqual(response.status_code, 415, response.text)
            self.assertIn("Content mismatch", response.json()["detail"])

    def test_upload_enforces_max_upload_bytes(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                max_upload_bytes=16,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", b"ISO-10303-21;EXTRA", "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 413, response.text)

    def test_upload_returns_sha256_and_sniffed_kind(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        payload = b"ISO-10303-21;\nENDSEC;\n"
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pilot.ifc", payload, "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body["sniffed_kind"], "ifc")
            self.assertEqual(body["size_bytes"], len(payload))
            self.assertEqual(len(body["sha256"]), 64)
            stored = Path(tmp) / body["path"]
            self.assertTrue(stored.is_file())
            self.assertFalse((Path(tmp) / "quarantine" / body["upload_id"] / "pilot.ifc").exists())

    def test_zip_bomb_members_rejected(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            for index in range(300):
                archive.writestr(f"m{index}.txt", b"x")
        payload = buf.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pack.zip", payload, "application/zip")},
            )
            self.assertEqual(response.status_code, 422, response.text)
            self.assertIn("too many members", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
