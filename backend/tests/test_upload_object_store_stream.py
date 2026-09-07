"""Upload ingest must stream to the object store off the event loop (issue #32).

Does not measure RSS and does not raise IFC caps. Not an OOM-closed claim.
"""

from __future__ import annotations

import asyncio
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore
from aerobim.domain.object_acl import LAB_ANONYMOUS_TENANT_ID
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.errors import public_upload_object_store_failed_detail

_IFC = b"ISO-10303-21;\n"
_UPLOADS_PY = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "aerobim"
    / "presentation"
    / "http"
    / "routes"
    / "uploads.py"
)


def _settings(root: Path) -> Settings:
    return Settings(
        application_name="aerobim-test",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=root,
        debug=True,
        allow_anonymous_dev=True,
    )


class _RecordingStore:
    def __init__(self) -> None:
        self.put_file_calls: list[tuple[str, Path, str | None]] = []
        self.put_bytes_calls: list[tuple[str, bytes, str | None]] = []
        self.deleted: list[str] = []
        self.blobs: dict[str, bytes] = {}

    def put_file(self, key: str, path: Path, *, content_type: str | None = None) -> str:
        source = Path(path)
        self.put_file_calls.append((key, source, content_type))
        self.blobs[key] = source.read_bytes()
        return key

    def put_bytes(self, key: str, payload: bytes, *, content_type: str | None = None) -> str:
        self.put_bytes_calls.append((key, payload, content_type))
        self.blobs[key] = payload
        return key

    def get_bytes(self, key: str) -> bytes | None:
        return self.blobs.get(key)

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.blobs.pop(key, None)

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None:
        del key, expires_in_seconds
        return None


class _BoomStore(_RecordingStore):
    def put_file(self, key: str, path: Path, *, content_type: str | None = None) -> str:
        del path, content_type
        raise RuntimeError(f"object store unavailable for {key}")


class _BlockingStore(_RecordingStore):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()

    def put_file(self, key: str, path: Path, *, content_type: str | None = None) -> str:
        del path
        self.put_file_calls.append((key, Path("."), content_type))
        self.started.set()
        if not self.release.wait(timeout=10):
            raise TimeoutError("put_file was not released")
        return key


def _app_with_store(root: Path, store: object):
    container = bootstrap_container(_settings(root))
    with patch(
        "aerobim.infrastructure.di._registrations_storage._build_object_store",
        return_value=store,
    ):
        return create_http_app(container)


class UploadObjectStoreSourceTests(unittest.TestCase):
    def test_object_store_branch_streams_via_put_file(self) -> None:
        source = _UPLOADS_PY.read_text(encoding="utf-8")
        branch = source[source.index("maybe_store") :]
        self.assertIn("put_file", branch)
        self.assertIn("asyncio.to_thread", branch)
        self.assertNotIn("read_bytes", branch)
        self.assertNotIn("put_bytes", branch)


class UploadObjectStoreStreamTests(unittest.TestCase):
    def test_upload_calls_put_file_not_put_bytes(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        store = _RecordingStore()
        with tempfile.TemporaryDirectory() as tmp:
            client = TestClient(_app_with_store(Path(tmp), store))
            response = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", _IFC, "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(len(store.put_file_calls), 1)
            self.assertEqual(store.put_bytes_calls, [])
            key, path, content_type = store.put_file_calls[0]
            self.assertEqual(key, body["path"])
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), _IFC)
            self.assertEqual(store.blobs[key], _IFC)
            self.assertTrue(content_type)

    def test_put_file_failure_unlinks_deletes_and_drops_quota(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        store = _BoomStore()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = TestClient(_app_with_store(root, store))
            response = client.post(
                "/v1/uploads",
                files={"file": ("model.ifc", _IFC, "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 500, response.text)
            self.assertEqual(response.json()["detail"], public_upload_object_store_failed_detail())
            self.assertEqual(len(store.deleted), 1)
            leftover = [path for path in root.rglob("*.ifc") if "quarantine" not in path.parts]
            self.assertEqual(leftover, [])
            quota = FilesystemUploadQuotaStore(root).snapshot(LAB_ANONYMOUS_TENANT_ID)
            holds = list((root / "quotas").glob("*/holds/*.json"))
            self.assertEqual((quota.bytes_used, quota.upload_count, len(holds)), (0, 0, 0))


class UploadObjectStoreEventLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_during_blocked_put_file(self) -> None:
        try:
            import httpx
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        store = _BlockingStore()
        with tempfile.TemporaryDirectory() as tmp:
            app = _app_with_store(Path(tmp), store)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                upload_task = asyncio.create_task(
                    client.post(
                        "/v1/uploads",
                        files={"file": ("model.ifc", _IFC, "application/octet-stream")},
                    )
                )
                started = await asyncio.to_thread(store.started.wait, 5)
                self.assertTrue(started)
                health = await client.get("/health")
                self.assertEqual(health.status_code, 200)
                self.assertEqual(health.json()["status"], "ok")
                store.release.set()
                uploaded = await upload_task
                self.assertEqual(uploaded.status_code, 200, uploaded.text)
                self.assertEqual(len(store.put_file_calls), 1)
                self.assertEqual(store.put_bytes_calls, [])

    async def test_cancel_during_put_file_cleans_up(self) -> None:
        try:
            import httpx
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        store = _BlockingStore()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = _app_with_store(root, store)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                upload_task = asyncio.create_task(
                    client.post(
                        "/v1/uploads",
                        files={"file": ("model.ifc", _IFC, "application/octet-stream")},
                    )
                )
                started = await asyncio.to_thread(store.started.wait, 5)
                self.assertTrue(started)
                upload_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await upload_task
                store.release.set()
                await asyncio.sleep(0.05)
            leftover = [path for path in root.rglob("*.ifc") if "quarantine" not in path.parts]
            self.assertEqual(leftover, [])
            self.assertEqual(len(store.deleted), 1)
            quota = FilesystemUploadQuotaStore(root).snapshot(LAB_ANONYMOUS_TENANT_ID)
            holds = list((root / "quotas").glob("*/holds/*.json"))
            self.assertEqual((quota.bytes_used, quota.upload_count, len(holds)), (0, 0, 0))
