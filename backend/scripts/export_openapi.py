"""Export the AeroBIM OpenAPI schema to a JSON file.

Usage:
    python scripts/export_openapi.py [output_path]

Default output path: docs/openapi.json (relative to repository root).

The script instantiates the FastAPI application without binding a network socket
so it is safe to run in CI without a running server.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ is importable when running from the backend directory.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def export_openapi(output_path: Path) -> None:
    settings = Settings.from_env()
    container = bootstrap_container(settings)
    app = create_http_app(container)
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OpenAPI schema written to {output_path} ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    default_output = (
        Path(__file__).parent.parent.parent / "docs" / "openapi.json"
    )
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    export_openapi(target)
