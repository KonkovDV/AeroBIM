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
                allow_anonymous_dev=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", b"%PDF-1.7\n", "application/pdf")},
            )
            self.assertEqual(response.status_code, 415, response.text)
            self.assertEqual(
                response.json()["detail"],
                "Upload content rejected",
            )

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
                allow_anonymous_dev=True,
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
                allow_anonymous_dev=True,
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

    def test_rejected_uploads_release_reserved_quota(self) -> None:
        """HD2-UP-01: 415/413/422 after reserve must release held_bytes (no quota leak)."""
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore

        def _snap(root: Path) -> tuple[int, int, int]:
            store = FilesystemUploadQuotaStore(root)
            quota = store.snapshot("anonymous-dev")
            holds = list((root / "quotas").glob("*/holds/*.json"))
            return quota.bytes_used, quota.upload_count, len(holds)

        def _settings(root: Path, **extra: object) -> Settings:
            values: dict[str, object] = {
                "application_name": "aerobim-test",
                "environment": "test",
                "host": "127.0.0.1",
                "port": 8080,
                "storage_dir": root,
                "debug": True,
                "max_upload_bytes": 1024,
                "max_uploads_per_tenant_day": 8,
                "max_upload_bytes_per_tenant_day": 50_000,
                "allow_anonymous_dev": True,
            }
            values.update(extra)
            return Settings(**values)  # type: ignore[arg-type]

        with tempfile.TemporaryDirectory() as tmp:
            container = bootstrap_container(_settings(Path(tmp)))
            client = TestClient(create_http_app(container))
            mismatch = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", b"%PDF-1.7\n", "application/pdf")},
            )
            self.assertEqual(mismatch.status_code, 415, mismatch.text)
            self.assertEqual(_snap(Path(tmp)), (0, 0, 0))

        with tempfile.TemporaryDirectory() as tmp:
            container = bootstrap_container(_settings(Path(tmp), max_upload_bytes=16))
            client = TestClient(create_http_app(container))
            oversize = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", b"ISO-10303-21;EXTRA", "application/octet-stream")},
            )
            self.assertEqual(oversize.status_code, 413, oversize.text)
            self.assertEqual(_snap(Path(tmp)), (0, 0, 0))

        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            for index in range(300):
                archive.writestr(f"m{index}.txt", b"x")
        with tempfile.TemporaryDirectory() as tmp:
            container = bootstrap_container(
                _settings(
                    Path(tmp), max_upload_bytes=200_000, max_upload_bytes_per_tenant_day=1_000_000
                )
            )
            client = TestClient(create_http_app(container))
            zipped = client.post(
                "/v1/uploads",
                files={"file": ("pack.zip", buf.getvalue(), "application/zip")},
            )
            self.assertEqual(zipped.status_code, 422, zipped.text)
            self.assertEqual(_snap(Path(tmp)), (0, 0, 0))

    def test_stream_413_handler_drops_quota(self) -> None:
        """HD2-UP-01: stream 413 must call _drop_quota() so held_bytes are released."""
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "presentation"
            / "http"
            / "routes"
            / "uploads.py"
        ).read_text(encoding="utf-8")
        self.assertIn("held_bytes = max_bytes", source)
        drop_start = source.index("def _drop_quota")
        drop_end = source.index("relative_path = ", drop_start)
        drop_fn = source[drop_start:drop_end]
        self.assertIn("size_bytes=held_bytes", drop_fn)
        self.assertIn("held_bytes = 0", drop_fn)
        oversize_at = source.index("if total > max_bytes:")
        handler = source[oversize_at:]
        http_exc_at = handler.index("except HTTPException:")
        drop_at = handler.index("_drop_quota()")
        self.assertLess(http_exc_at, drop_at)

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
                allow_anonymous_dev=True,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pack.zip", payload, "application/zip")},
            )
            self.assertEqual(response.status_code, 422, response.text)
            self.assertEqual(response.json()["detail"], "Upload archive rejected")


if __name__ == "__main__":
    unittest.main()
