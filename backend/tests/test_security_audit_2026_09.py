"""External static-audit remediations (RL-01, RL-02, OPS-01) — September 2026."""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.rate_limit import (
    _RATE_LIMIT_POST_ALLOWLIST,
    add_rate_limit_middleware,
    post_path_is_rate_limited,
)


def _iter_http_routes(app: object) -> list[object]:
    found: list[object] = []

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
            found.append(route)

    walk(app.routes)  # type: ignore[attr-defined]
    return found


def _sample_path(route_path: str) -> str:
    return re.sub(r"\{[^}]+\}", "id", route_path)


class PreAuthRateLimitTests(unittest.TestCase):
    def test_token_spray_from_one_ip_hits_429(self) -> None:
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        app = FastAPI()
        add_rate_limit_middleware(app, requests_per_minute=100)

        @app.post("/v1/analyze/project-package")
        def _noop() -> dict[str, str]:
            return {"ok": "1"}

        client = TestClient(app)
        statuses = [
            client.post(
                "/v1/analyze/project-package",
                headers={"Authorization": f"Bearer spray-{index}"},
            ).status_code
            for index in range(200)
        ]
        self.assertIn(429, statuses)
        self.assertGreaterEqual(statuses.count(429), 1)

    def test_uploads_exact_path_is_rate_limited(self) -> None:
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        app = FastAPI()
        add_rate_limit_middleware(app, requests_per_minute=3)

        @app.post("/v1/uploads")
        def _noop() -> dict[str, str]:
            return {"ok": "1"}

        client = TestClient(app)
        codes = [client.post("/v1/uploads").status_code for _ in range(5)]
        self.assertIn(429, codes)

    def test_every_v1_post_is_limited_or_allowlisted(self) -> None:
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
                http_rate_limit_per_minute=0,
            )
            app = create_http_app(bootstrap_container(settings))
            TestClient(app)
            missing: list[str] = []
            for route in _iter_http_routes(app):
                methods = getattr(route, "methods", None) or set()
                if "POST" not in methods:
                    continue
                path = str(getattr(route, "path", "") or "")
                if not path.startswith("/v1/"):
                    continue
                sample = _sample_path(path)
                if post_path_is_rate_limited(sample):
                    continue
                if path in _RATE_LIMIT_POST_ALLOWLIST or sample in _RATE_LIMIT_POST_ALLOWLIST:
                    continue
                missing.append(path)
            self.assertEqual(
                missing,
                [],
                "POST /v1/* must be rate-limited or listed in _RATE_LIMIT_POST_ALLOWLIST "
                "with a justification comment: " + ", ".join(missing),
            )


class ProductionComposeHardeningTests(unittest.TestCase):
    def test_ops01_compose_hardening_keys(self) -> None:
        root = Path(__file__).resolve().parents[2]
        text = (root / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("read_only: true", text)
        self.assertIn("/tmp", text)
        self.assertIn("cap_drop:", text)
        self.assertIn("ALL", text)
        self.assertIn("no-new-privileges:true", text)
        self.assertIn("pids_limit:", text)
        self.assertIn("--requirepass", text)
        self.assertIn("AEROBIM_REDIS_PASSWORD:?", text)


if __name__ == "__main__":
    unittest.main()
