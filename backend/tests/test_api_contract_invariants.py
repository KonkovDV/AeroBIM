"""H0.3: refactor-parity audit institutionalized as CI contract tests.

Origin: the Red Team refactor audit proved parity between the api.py monolith
and the extracted HTTP corpus with one-shot scripts (.local/audit_runtime_probes.py,
.local/dump_openapi_snapshot.py). These invariants are now permanent:

1. OpenAPI snapshot — the normalized schema of ``create_http_app`` must match
   the committed snapshot (``tests/contracts/openapi_contract_snapshot.json``).
   Deliberate contract changes are made by regenerating the snapshot:

       AEROBIM_UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/test_api_contract_invariants.py

   and committing the diff for review. Silent drift fails CI.

2. Auth gate — every ``/v1`` route must carry the ``require_bearer_auth``
   dependency except the explicit no-auth allowlist; the allowlist itself is
   asserted both ways so it cannot rot. All routes must share one bound-method
   callable (FastAPI per-request dependency cache key parity).

3. Orchestrator host contract — every ``self._host.<method>()`` call inside
   ``analyze_orchestrators`` must resolve to an attribute of
   ``AnalyzeProjectPackageUseCase``.

Falsifiability: deleting a ``Depends(ctx.require_bearer_auth)``, renaming a
route, or removing a use-case host method must fail this module.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import unittest
from pathlib import Path

from aerobim.tools.export_api_contract_summary import _build_contract_summary_app

SNAPSHOT_PATH = Path(__file__).parent / "contracts" / "openapi_contract_snapshot.json"
UPDATE_ENV = "AEROBIM_UPDATE_OPENAPI_SNAPSHOT"

# Public, unauthenticated surface. Adding a path here is a security decision
# and must be reviewed together with the route change.
ALLOW_NO_AUTH = frozenset({"/health", "/v1/auth/bff"})

_HOST_CALL = re.compile(r"self\._host\.(_?[a-zA-Z_]+)\(")


def _build_app():
    app, _settings = _build_contract_summary_app()
    return app


def _normalized_openapi(app) -> str:
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True)


def _operations(schema: dict) -> set[str]:
    ops: set[str] = set()
    for path, methods in schema.get("paths", {}).items():
        if isinstance(methods, dict):
            for method in methods:
                ops.add(f"{method.upper()} {path}")
    return ops


class OpenApiSnapshotTests(unittest.TestCase):
    """Invariant 1: the HTTP contract only changes through a reviewed snapshot diff."""

    def test_openapi_matches_committed_snapshot(self) -> None:
        actual = _normalized_openapi(_build_app())

        if os.getenv(UPDATE_ENV, "").strip() in {"1", "true", "yes"}:
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            SNAPSHOT_PATH.write_text(actual + "\n", encoding="utf-8")
            self.skipTest(f"snapshot regenerated at {SNAPSHOT_PATH}; commit and review the diff")

        self.assertTrue(
            SNAPSHOT_PATH.is_file(),
            f"Missing OpenAPI snapshot {SNAPSHOT_PATH}; "
            f"generate it with {UPDATE_ENV}=1 pytest {Path(__file__).name}",
        )
        expected = SNAPSHOT_PATH.read_text(encoding="utf-8").rstrip("\n")

        if actual == expected:
            return

        # Summarize drift at operation level before failing so CI output is actionable.
        actual_ops = _operations(json.loads(actual))
        expected_ops = _operations(json.loads(expected))
        added = sorted(actual_ops - expected_ops)
        removed = sorted(expected_ops - actual_ops)
        self.fail(
            "OpenAPI contract drifted from the committed snapshot.\n"
            f"  added operations:   {added or '(none — schema-level change)'}\n"
            f"  removed operations: {removed or '(none — schema-level change)'}\n"
            f"If this change is intentional, regenerate with "
            f"{UPDATE_ENV}=1 and commit the snapshot diff."
        )


class AuthGateTests(unittest.TestCase):
    """Invariant 2: no /v1 route ships without the bearer-auth dependency."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = _build_app()

    @staticmethod
    def _dependency_calls(route) -> list[object]:
        calls: list[object] = []

        def walk(dep) -> None:
            calls.append(dep.call)
            for sub in dep.dependencies:
                walk(sub)

        walk(route.dependant)
        return calls

    def _service_routes(self):
        # FastAPI >= 0.140 wraps included routers lazily (_IncludedRouter):
        # app.routes no longer flattens them, so walk nested routers too.
        # Version-tolerant: flat APIRoute lists (<= 0.139) still work.
        def walk_routes(routes):
            for route in routes:
                inner = getattr(route, "original_router", None)
                if inner is not None:
                    yield from walk_routes(inner.routes)
                    continue
                nested = getattr(route, "routes", None)
                if nested is not None and not hasattr(route, "dependant"):
                    yield from walk_routes(nested)
                    continue
                yield route

        for route in walk_routes(self.app.routes):
            path = getattr(route, "path", "")
            if getattr(route, "dependant", None) is None:
                continue
            if path.startswith(("/health", "/v1")):
                yield path, route

    def test_every_service_route_is_authenticated_or_allowlisted(self) -> None:
        failures: list[str] = []
        checked = 0
        for path, route in self._service_routes():
            checked += 1
            has_auth = any(
                getattr(call, "__name__", "") == "require_bearer_auth"
                for call in self._dependency_calls(route)
                if call is not None
            )
            if path in ALLOW_NO_AUTH:
                if has_auth:
                    failures.append(f"{path}: allowlisted but carries auth (stale allowlist)")
            elif not has_auth:
                failures.append(f"{path}: MISSING require_bearer_auth dependency")
        self.assertGreater(checked, 0, "no /health or /v1 routes found — app wiring broken")
        self.assertEqual(failures, [])

    def test_allowlist_paths_all_exist(self) -> None:
        paths = {path for path, _route in self._service_routes()}
        missing = sorted(ALLOW_NO_AUTH - paths)
        self.assertEqual(missing, [], "allowlist references routes that no longer exist")

    def test_auth_dependency_is_one_shared_bound_method(self) -> None:
        distinct: set[int] = set()
        for _path, route in self._service_routes():
            for call in self._dependency_calls(route):
                if call is not None and getattr(call, "__name__", "") == "require_bearer_auth":
                    distinct.add(id(call.__func__) if hasattr(call, "__func__") else id(call))
        self.assertEqual(
            len(distinct),
            1,
            "require_bearer_auth must be one shared callable so FastAPI's "
            "per-request dependency cache key stays identical across routers",
        )


class OrchestratorHostContractTests(unittest.TestCase):
    """Invariant 3: orchestrators only call methods the use-case host still exposes."""

    def test_every_host_call_resolves_on_use_case(self) -> None:
        import aerobim.application.services.analyze_orchestrators as orchestrators
        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )

        source = inspect.getsource(orchestrators)
        host_methods = sorted(set(_HOST_CALL.findall(source)))
        self.assertGreater(len(host_methods), 0, "no self._host.<method>() calls found")
        missing = [
            method for method in host_methods if not hasattr(AnalyzeProjectPackageUseCase, method)
        ]
        self.assertEqual(
            missing,
            [],
            "orchestrators call host methods missing on AnalyzeProjectPackageUseCase",
        )


if __name__ == "__main__":
    unittest.main()
