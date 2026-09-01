"""HTTP revision-diff is verdict-neutral and does not claim resolved."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class RevisionDiffHttpTests(unittest.TestCase):
    def test_two_fixture_runs_are_still_reported_not_resolved(self) -> None:
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
            first = client.post("/v1/demo/seed-fixture")
            second = client.post("/v1/demo/seed-fixture")
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(second.status_code, 200, second.text)
            old_id = first.json()["report_id"]
            new_id = second.json()["report_id"]
            self.assertNotEqual(old_id, new_id)
            same = client.get(f"/v1/reports/{old_id}/revision-diff?against={old_id}")
            self.assertEqual(same.status_code, 400)
            diff = client.get(f"/v1/reports/{old_id}/revision-diff?against={new_id}")
            self.assertEqual(diff.status_code, 200, diff.text)
            payload = diff.json()
            self.assertEqual(payload["artifact"], "revision-diff")
            self.assertNotIn("passed", payload)
            self.assertIn("does NOT claim", payload["note"])
            self.assertGreaterEqual(len(payload["still_reported"]), 1)
            self.assertEqual(payload["summary"]["newly_reported"], 0)
            self.assertEqual(payload["summary"]["no_longer_reported"], 0)


if __name__ == "__main__":
    unittest.main()
