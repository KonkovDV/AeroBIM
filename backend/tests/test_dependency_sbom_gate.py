"""P-001 SBOM gate: the committed backend SBOM must exist, be structurally
CycloneDX, and cover every verified core dependency from the license inventory
(pymupdf's dual license can never silently vanish from the SBOM)."""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SBOM = _REPO_ROOT / "docs" / "evidence" / "sbom-backend-latest.json"
_INVENTORY = _REPO_ROOT / "audit" / "dependency_license_inventory.json"


def _sbom() -> dict[str, object]:
    payload = json.loads(_SBOM.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_sbom_exists_and_is_cyclonedx() -> None:
    payload = _sbom()
    assert payload["bomFormat"] == "CycloneDX"
    assert payload["specVersion"]
    components = payload["components"]
    assert isinstance(components, list) and len(components) >= 10


def test_sbom_covers_verified_core_dependencies() -> None:
    inventory = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    core = {
        str(item["name"]).lower()
        for item in inventory["dependencies"]
        if isinstance(item, dict)
        and str(item.get("scope", "")).startswith("core")
        and item.get("verified") is True
    }
    sbom_names = {
        str(component["name"]).lower()
        for component in _sbom()["components"]  # type: ignore[union-attr]
        if isinstance(component, dict)
    }
    missing = sorted(core - sbom_names)
    assert not missing, f"Verified core deps missing from SBOM: {missing}"


def test_sbom_pins_pymupdf_dual_license() -> None:
    components = [
        c
        for c in _sbom()["components"]  # type: ignore[union-attr]
        if isinstance(c, dict) and str(c.get("name", "")).lower() == "pymupdf"
    ]
    assert components, "pymupdf must be present in the backend SBOM (LIC-001)"
    license_name = str(components[0]["licenses"][0]["license"]["name"])  # type: ignore[index]
    assert "AFFERO" in license_name.upper() or "AGPL" in license_name.upper()


def test_sbom_declares_honest_scope() -> None:
    props = _sbom()["metadata"]["properties"]  # type: ignore[index]
    scope = next(p["value"] for p in props if p["name"] == "aerobim:scope")  # type: ignore[index]
    assert "NOT covered" in scope
