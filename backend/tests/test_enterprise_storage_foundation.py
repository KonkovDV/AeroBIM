from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aerobim.core.security.object_limits import ObjectTooLargeError
from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.s3_object_store import S3ObjectStore


def _make_report(
    report_id: str,
    *,
    ifc_path: Path,
    created_at: str | None = None,
) -> ValidationReport:
    return ValidationReport(
        report_id=report_id,
        request_id=f"req-{report_id[:8]}",
        ifc_path=ifc_path,
        created_at=created_at or datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=0,
            error_count=0,
            warning_count=0,
            passed=True,
        ),
    )


class FakeBody:
    """Minimal StreamingBody stand-in with chunked ``read(amt)``."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def read(self, amt: int | None = None) -> bytes:
        if self._pos >= len(self._data):
            return b""
        if amt is None:
            chunk = self._data[self._pos :]
            self._pos = len(self._data)
            return chunk
        end = min(self._pos + amt, len(self._data))
        chunk = self._data[self._pos : end]
        self._pos = end
        return chunk


class LocalObjectStoreTests(unittest.TestCase):
    def test_put_get_delete_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir))

            key = store.put_bytes("drawing-assets/report-1/preview.png", b"png-bytes")
            self.assertEqual(store.get_bytes(key), b"png-bytes")
            self.assertIsNotNone(store.presign_get(key))

            store.delete(key)
            self.assertIsNone(store.get_bytes(key))

    def test_get_bytes_rejects_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir), max_get_bytes=8)
            key = store.put_bytes("big.bin", b"0123456789")
            with self.assertRaises(ObjectTooLargeError):
                store.get_bytes(key)


class FilesystemAuditStoreEnterpriseFoundationTests(unittest.TestCase):
    def test_save_copies_ifc_source_into_object_store_and_roundtrips_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            ifc_path = storage_dir / "model.ifc"
            ifc_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

            store = FilesystemAuditStore(storage_dir)
            report = _make_report("c" * 32, ifc_path=ifc_path)

            store.save(report)
            loaded = store.get(report.report_id)

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertIsNotNone(loaded.ifc_object_key)
            self.assertTrue((storage_dir / str(loaded.ifc_object_key)).exists())

    def test_get_prunes_reports_older_than_ttl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            ifc_path = storage_dir / "expired.ifc"
            ifc_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")

            store = FilesystemAuditStore(storage_dir, report_ttl_days=1)
            expired_report = _make_report(
                "d" * 32,
                ifc_path=ifc_path,
                created_at=(datetime.now(tz=UTC) - timedelta(days=3)).isoformat(),
            )
            store.save(expired_report)

            self.assertIsNone(store.get(expired_report.report_id))
            self.assertEqual(store.list_reports(), [])
            self.assertFalse(
                (storage_dir / "reports" / f"{expired_report.report_id}.json").exists()
            )


class S3ObjectStoreTests(unittest.TestCase):
    def _patch_fake_client(self, stored_objects: dict[str, bytes]):
        class NoSuchKeyError(Exception):
            pass

        class FakeS3Client:
            class exceptions:
                NoSuchKey = NoSuchKeyError

            def put_object(self, *, Bucket: str, Key: str, Body: bytes, **_: object) -> None:
                stored_objects[Key] = Body

            def get_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
                if Key not in stored_objects:
                    raise NoSuchKeyError()
                payload = stored_objects[Key]
                return {
                    "Body": FakeBody(payload),
                    "ContentLength": len(payload),
                }

            def delete_object(self, *, Bucket: str, Key: str) -> None:
                stored_objects.pop(Key, None)

            def generate_presigned_url(
                self,
                method: str,
                *,
                Params: dict[str, str],
                ExpiresIn: int,
            ) -> str:
                return f"{method}:{Params['Key']}:{ExpiresIn}"

        fake_boto3 = SimpleNamespace(client=lambda *args, **kwargs: FakeS3Client())
        fake_botocore_config = SimpleNamespace(Config=lambda **kwargs: object())
        return patch.dict(
            sys.modules,
            {
                "boto3": fake_boto3,
                "botocore.config": fake_botocore_config,
            },
        )

    def test_qualified_key_roundtrip_is_idempotent_for_persisted_keys(self) -> None:
        stored_objects: dict[str, bytes] = {}
        with self._patch_fake_client(stored_objects):
            store = S3ObjectStore(bucket="bucket", region="ru-test-1", prefix="aerobim")

            key = store.put_bytes("ifc-sources/report-1/model.ifc", b"ifc-bytes")

            self.assertEqual(key, "aerobim/ifc-sources/report-1/model.ifc")
            self.assertEqual(store.get_bytes(key), b"ifc-bytes")
            self.assertEqual(
                store.presign_get(key, expires_in_seconds=60),
                "get_object:aerobim/ifc-sources/report-1/model.ifc:60",
            )

            store.delete(key)
            self.assertIsNone(store.get_bytes(key))

    def test_get_bytes_rejects_oversized_content_length(self) -> None:
        stored_objects: dict[str, bytes] = {}
        with self._patch_fake_client(stored_objects):
            store = S3ObjectStore(
                bucket="bucket",
                region="ru-test-1",
                prefix="aerobim",
                max_get_bytes=8,
            )
            key = store.put_bytes("ifc-sources/report-1/model.ifc", b"0123456789")
            with self.assertRaises(ObjectTooLargeError):
                store.get_bytes(key)

    def test_get_bytes_rejects_when_stream_exceeds_cap_without_length(self) -> None:
        class NoSuchKeyError(Exception):
            pass

        class FakeS3Client:
            class exceptions:
                NoSuchKey = NoSuchKeyError

            def get_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
                del Bucket, Key
                return {"Body": FakeBody(b"0123456789")}

        fake_boto3 = SimpleNamespace(client=lambda *args, **kwargs: FakeS3Client())
        fake_botocore_config = SimpleNamespace(Config=lambda **kwargs: object())
        with patch.dict(
            sys.modules,
            {
                "boto3": fake_boto3,
                "botocore.config": fake_botocore_config,
            },
        ):
            store = S3ObjectStore(
                bucket="bucket",
                region="ru-test-1",
                prefix="aerobim",
                max_get_bytes=8,
            )
            with self.assertRaises(ObjectTooLargeError):
                store.get_bytes("aerobim/any")
