"""Upload quota + orphan reconciliation residual tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.security.upload_quota import (
    FilesystemUploadQuotaStore,
    UploadQuotaExceeded,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.tools.reconcile_audit_orphans import reconcile_orphans


class UploadQuotaTests(unittest.TestCase):
    def test_count_quota_blocks_second_upload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = FilesystemUploadQuotaStore(
                Path(temporary_directory),
                max_uploads_per_day=1,
                max_bytes_per_day=10_000,
            )
            store.assert_can_accept("t1", size_bytes=10)
            store.record("t1", size_bytes=10)
            with self.assertRaises(UploadQuotaExceeded):
                store.assert_can_accept("t1", size_bytes=10)

    def test_api_returns_429_when_quota_exceeded(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        payload = b"ISO-10303-21;\n"
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                max_uploads_per_tenant_day=1,
            )
            container = bootstrap_container(settings)
            client = TestClient(create_http_app(container))
            first = client.post(
                "/v1/uploads",
                files={"file": ("a.ifc", payload, "application/octet-stream")},
            )
            self.assertEqual(first.status_code, 200, first.text)
            second = client.post(
                "/v1/uploads",
                files={"file": ("b.ifc", payload, "application/octet-stream")},
            )
            self.assertEqual(second.status_code, 429, second.text)


class OrphanReconcileTests(unittest.TestCase):
    def test_dry_run_and_apply_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            orphan_dir = root / "orphans"
            orphan_dir.mkdir(parents=True)
            report_id = "f" * 32
            object_key = f"ifc-sources/{report_id}/model.ifc"
            # Write orphan record only; apply must remove the orphan JSON.
            (orphan_dir / f"{report_id}.json").write_text(
                json.dumps(
                    {
                        "report_id": report_id,
                        "artifact_keys": [object_key],
                        "consistency_state": "orphan_uncommitted",
                    }
                ),
                encoding="utf-8",
            )
            dry = reconcile_orphans(root, apply=False)
            self.assertEqual(dry["orphan_count"], 1)
            self.assertEqual(dry["records"][0]["status"], "orphan_uncommitted")

            applied = reconcile_orphans(root, apply=True)
            self.assertEqual(applied["records"][0]["status"], "cleaned_uncommitted")
            self.assertFalse((orphan_dir / f"{report_id}.json").exists())


if __name__ == "__main__":
    unittest.main()
