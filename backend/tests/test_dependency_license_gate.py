"""P-001 license gate: every declared backend dependency must be classified in
audit/dependency_license_inventory.json; unknown or release-blocking licenses
fail CI (engineering gate, NOT a legal opinion)."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INVENTORY = _REPO_ROOT / "audit" / "dependency_license_inventory.json"
_PYPROJECT = _REPO_ROOT / "backend" / "pyproject.toml"

_ALLOWED_RISK = {"permissive", "weak_copyleft", "strong_copyleft_or_commercial"}


def _inventory() -> dict[str, dict[str, object]]:
    data = json.loads(_INVENTORY.read_text(encoding="utf-8"))
    deps = data["dependencies"]
    assert isinstance(deps, list) and deps
    return {str(item["name"]).lower(): item for item in deps if isinstance(item, dict)}


def _declared_dependencies() -> set[str]:
    payload = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    names: set[str] = set()
    groups: list[list[str]] = [payload["project"]["dependencies"]]
    for group, items in payload["project"].get("optional-dependencies", {}).items():
        if group == "dev":
            continue  # dev tools are not shipped
        groups.append(items)
    for group_items in groups:
        for spec in group_items:
            name = re.split(r"[<>=!\[;\s]", spec.strip(), maxsplit=1)[0]
            if name:
                names.add(name.lower())
    return names


def test_every_shipped_dependency_is_classified() -> None:
    inventory = _inventory()
    missing = sorted(_declared_dependencies() - set(inventory))
    assert not missing, (
        "Dependencies without a license classification (add them to "
        f"audit/dependency_license_inventory.json): {missing}"
    )


def test_no_unknown_risk_class() -> None:
    bad = [
        name
        for name, item in _inventory().items()
        if str(item.get("risk_class")) not in _ALLOWED_RISK
    ]
    assert not bad, f"Unclassified/unknown license risk blocks release: {sorted(bad)}"


def test_copyleft_and_commercial_entries_flag_legal_review() -> None:
    bad = [
        name
        for name, item in _inventory().items()
        if str(item.get("risk_class")) in {"weak_copyleft", "strong_copyleft_or_commercial"}
        and item.get("legal_review_required") is not True
    ]
    assert not bad, (
        f"Copyleft/dual-commercial entries must carry legal_review_required=true: {sorted(bad)}"
    )


def test_frontend_runtime_dependencies_are_classified() -> None:
    # Direct runtime deps of the browser shell must carry a license classification;
    # dev tooling (vite/vitest/types) is not shipped and stays out of scope.
    package_json = _REPO_ROOT / "frontend" / "package.json"
    payload = json.loads(package_json.read_text(encoding="utf-8"))
    runtime = {name.lower() for name in (payload.get("dependencies") or {})}
    missing = sorted(runtime - set(_inventory()))
    assert not missing, f"Frontend runtime deps without license classification: {missing}"


def test_web_ifc_mpl_is_acknowledged() -> None:
    # VERIFIED 2026-07-31: web-ifc 0.0.77 declares MPL-2.0 (file-level copyleft).
    item = _inventory()["web-ifc"]
    assert item["risk_class"] == "weak_copyleft"
    assert item["legal_review_required"] is True


def test_pymupdf_dual_license_is_acknowledged() -> None:
    # VERIFIED 2026-07-31 from installed wheel metadata: pymupdf 1.27.x declares
    # "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License" and is a
    # MANDATORY core dependency -- the inventory must never silently drop this.
    item = _inventory()["pymupdf"]
    assert item["risk_class"] == "strong_copyleft_or_commercial"
    assert item["legal_review_required"] is True
    assert item["scope"] == "core"
