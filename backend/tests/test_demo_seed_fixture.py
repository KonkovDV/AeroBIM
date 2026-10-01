"""Development demo fixture seed is live in the review shell; production 404."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.rate_limit import _RATE_LIMITED_POST_PREFIXES
from aerobim.presentation.http.routes.demo import _resolved_sample, materialize_demo_pack


def _route_paths(app: object) -> set[str]:
    paths: set[str] = set()

    def walk(routes: object) -> None:
        for route in routes:  # type: ignore[union-attr]
            inner = getattr(route, "original_router", None)
            if inner is not None:
                walk(inner.routes)
                continue
            nested = getattr(route, "routes", None)
            if nested is not None and not hasattr(route, "dependant"):
                walk(nested)
                continue
            path = getattr(route, "path", "")
            if path:
                paths.add(path)

    walk(app.routes)  # type: ignore[attr-defined]
    return paths


class DemoSeedFixtureTests(unittest.TestCase):
    def test_demo_posts_are_rate_limited_like_other_mutators(self) -> None:
        self.assertIn("/v1/demo/", _RATE_LIMITED_POST_PREFIXES)

    def test_seed_fixture_returns_report_and_stays_no_go(self) -> None:
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
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.post("/v1/demo/seed-fixture")
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            self.assertTrue(payload["fixture"])
            self.assertEqual(payload["checkpoint"], CHECKPOINT)
            self.assertFalse(payload["closes_rt001"])
            self.assertNotIn("passed", payload)
            self.assertGreaterEqual(int(payload["issue_count"]), 1)
            self.assertRegex(str(payload["report_id"]), r"^[a-f0-9]{32}$")
            dest_ifc = Path(tmp) / "demo-fixture" / "walls-multi-entity-spatial.ifc"
            self.assertTrue(dest_ifc.is_file())
            dest_ids = Path(tmp) / "demo-fixture" / "walls-multi-entity.ids"
            self.assertTrue(dest_ids.is_file())
            dest_pdf = Path(tmp) / "demo-fixture" / "techlab-a101-wall-thickness.pdf"
            self.assertTrue(dest_pdf.is_file())
            listed = client.get("/v1/reports")
            self.assertEqual(listed.status_code, 200)
            ids = [row["report_id"] for row in listed.json()["reports"]]
            self.assertIn(payload["report_id"], ids)
            report = client.get(f"/v1/reports/{payload['report_id']}")
            self.assertEqual(report.status_code, 200)
            body = report.json()
            self.assertFalse(body["summary"]["passed"])
            self.assertGreaterEqual(int(body["summary"]["generated_remark_count"]), 1)
            remarks = [issue.get("remark") or {} for issue in body["issues"]]
            self.assertTrue(
                any(str(remark.get("clause_cite") or "").startswith("ТЗ") for remark in remarks),
                "demo pack must bind remarks to the ТЗ clause",
            )
            self.assertGreaterEqual(len(body.get("drawing_assets") or []), 1)
            if payload.get("drawing_asset_id"):
                asset_ids = [asset["asset_id"] for asset in body["drawing_assets"]]
                self.assertIn(payload["drawing_asset_id"], asset_ids)
            bcf = client.get(f"/v1/reports/{payload['report_id']}/export/bcf")
            self.assertEqual(bcf.status_code, 200)
            self.assertIn("/v1/demo/seed-fixture", _route_paths(client.app))
            self.assertNotIn("/v1/demo/seed-fixture", client.app.openapi().get("paths", {}))

    def test_seed_fixture_hidden_outside_dev(self) -> None:
        try:
            from fastapi.testclient import TestClient

        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="production",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=False,
                allow_anonymous_dev=False,
                api_bearer_token="unit-test-demo-seed-token-32chars",
            )
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.post(
                "/v1/demo/seed-fixture",
                headers={"Authorization": "Bearer unit-test-demo-seed-token-32chars"},
            )
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("/v1/demo/seed-fixture", _route_paths(client.app))
            anonymous = client.post("/v1/demo/seed-fixture")
            self.assertEqual(anonymous.status_code, 404)


class DemoSampleJailTests(unittest.TestCase):
    def test_resolved_sample_rejects_escape_outside_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "samples").mkdir()
            secret = root / "secret.txt"
            secret.write_text("nope", encoding="utf-8")
            with self.assertRaises(ValueError):
                _resolved_sample(root, "secret.txt")
            with self.assertRaises(ValueError):
                _resolved_sample(root, "../secret.txt")

    def test_materialize_rejects_manifest_path_outside_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            storage = root / "storage"
            storage.mkdir()
            manifest_dir = root / "samples" / "demo" / "vertical-slice-2026-08-11"
            manifest_dir.mkdir(parents=True)
            (root / "samples" / "ok.ifc").write_text("ISO", encoding="utf-8")
            (root / "outside.ids").write_text("<ids/>", encoding="utf-8")
            manifest = {
                "discipline": "architecture",
                "stage": "demo",
                "request": {
                    "ifc_path": "samples/ok.ifc",
                    "ids_path": "outside.ids",
                    "requirement_path": "samples/ok.ifc",
                    "technical_spec_path": "samples/ok.ifc",
                    "calculation_path": "samples/ok.ifc",
                    "drawings": [],
                },
            }
            (manifest_dir / "manifest.json").write_text(
                __import__("json").dumps(manifest), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                materialize_demo_pack(storage, root)


if __name__ == "__main__":
    unittest.main()
