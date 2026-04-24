from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.presentation.http.api import create_http_app


class _NullLogger:
    def info(self, message: str, **context: object) -> None:
        pass

    def warning(self, message: str, **context: object) -> None:
        pass

    def error(self, message: str, **context: object) -> None:
        pass

    def debug(self, message: str, **context: object) -> None:
        pass


class _NoOpValidateUseCase:
    def execute(self, request):
        raise RuntimeError("No-op validate use case for contract summary export")


class _NoOpAnalyzeUseCase:
    def execute(self, request):
        raise RuntimeError("No-op analyze use case for contract summary export")


def _build_contract_summary_app():
    storage = Path("var").resolve()
    storage.mkdir(parents=True, exist_ok=True)

    settings = Settings(
        application_name="aerobim-backend",
        environment="contract-summary",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage,
        debug=False,
        cors_origins=(
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ),
    )

    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _NullLogger())
    container.register(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE, lambda _: _NoOpValidateUseCase())
    container.register(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE, lambda _: _NoOpAnalyzeUseCase())
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: InMemoryAuditStore())
    return create_http_app(container), settings


def _collect_contract_summary(app) -> dict[str, object]:
    openapi = app.openapi()
    paths = openapi.get("paths", {}) if isinstance(openapi, dict) else {}

    route_items: list[dict[str, object]] = []
    for route_path in sorted(paths.keys()):
        methods = paths.get(route_path, {})
        if not isinstance(methods, dict):
            continue
        for method in sorted(methods.keys()):
            operation = methods.get(method, {})
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            if isinstance(responses, dict):
                response_codes = sorted(str(code) for code in responses.keys())
            else:
                response_codes = []
            request_body_required = False
            if isinstance(operation.get("requestBody"), dict):
                request_body_required = bool(operation["requestBody"].get("required", False))
            route_items.append(
                {
                    "method": method.upper(),
                    "path": route_path,
                    "operation_id": operation.get("operationId"),
                    "response_codes": response_codes,
                    "request_body_required": request_body_required,
                }
            )

    return {
        "artifact_type": "api_contract_summary",
        "version": "v1",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "openapi_version": openapi.get("openapi") if isinstance(openapi, dict) else None,
        "service": openapi.get("info", {}).get("title") if isinstance(openapi, dict) else None,
        "route_count": len(route_items),
        "routes": route_items,
        "key_endpoints": [
            {
                "endpoint": "/health",
                "expected_status": ["200"],
                "contract_shape": ["service", "environment", "status"],
            },
            {
                "endpoint": "/v1/reports",
                "expected_status": ["200"],
                "contract_shape": ["reports", "count"],
            },
            {
                "endpoint": "/v1/analyze/project-package/reinforcement-digest",
                "expected_status": ["200", "400", "404"],
                "contract_shape": [
                    "reinforcement_report_path",
                    "provenance_digest",
                    "contract_id",
                    "schema_version",
                    "project_code",
                    "slab_id",
                ],
            },
        ],
    }


def main() -> None:
    app, settings = _build_contract_summary_app()
    payload = _collect_contract_summary(app)

    out_dir = settings.storage_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "aerobim_api_contract_summary_v1.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
