"""Export a CycloneDX-format SBOM for the backend Python environment (P-001).

Honest scope: ENGINEERING SBOM of the *current interpreter environment*
(importlib.metadata over installed distributions). It does NOT cover Docker
base images, the frontend npm tree, or wheels absent from this environment —
those stay listed in ``audit/dependency_license_inventory.json`` unknowns.
No third-party SBOM tooling required (stdlib only), so the generator itself
adds zero supply-chain surface.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

_SCHEMA_VERSION = "1.5"


def _license_text(dist: metadata.Distribution) -> str:
    md = dist.metadata
    expression = md.get("License-Expression")
    if expression:
        return str(expression)
    classifiers = [
        c.split("::")[-1].strip()
        for c in (md.get_all("Classifier") or [])
        if c.startswith("License")
    ]
    if classifiers:
        return "; ".join(classifiers)
    return str(md.get("License") or "UNKNOWN")


def build_sbom() -> dict[str, object]:
    components: list[dict[str, object]] = []
    for dist in sorted(metadata.distributions(), key=lambda d: (d.metadata["Name"] or "").lower()):
        name = dist.metadata["Name"]
        if not name:
            continue
        version = dist.version or "0"
        components.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name.lower()}@{version}",
                "licenses": [{"license": {"name": _license_text(dist)}}],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": _SCHEMA_VERSION,
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "tools": [{"name": "aerobim-export-dependency-sbom", "version": "1.0.0"}],
            "component": {"type": "application", "name": "aerobim-backend"},
            "properties": [
                {
                    "name": "aerobim:scope",
                    "value": (
                        "engineering SBOM of the current Python environment only; "
                        "Docker images and frontend npm tree NOT covered "
                        "(see audit/dependency_license_inventory.json)"
                    ),
                }
            ],
        },
        "components": components,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CycloneDX-format backend SBOM")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[3].parent
        / "docs"
        / "evidence"
        / "sbom-backend-latest.json",
    )
    args = parser.parse_args()
    payload = build_sbom()
    components = payload["components"]
    assert isinstance(components, list)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SBOM written: {args.out} ({len(components)} components)")


if __name__ == "__main__":
    main()
