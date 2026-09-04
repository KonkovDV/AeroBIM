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
            dest_ifc = Path(tmp) / "demo-fixture" / "walls-multi-entity.ifc"
            self.assertTrue(dest_ifc.is_file())
            listed = client.get("/v1/reports")
            self.assertEqual(listed.status_code, 200)
            ids = [row["report_id"] for row in listed.json()["reports"]]
            self.assertIn(payload["report_id"], ids)
            report = client.get(f"/v1/reports/{payload['report_id']}")
            self.assertEqual(report.status_code, 200)
            self.assertFalse(report.json()["summary"]["passed"])
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


if __name__ == "__main__":
    unittest.main()
