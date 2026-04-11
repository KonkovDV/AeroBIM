# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

"""Architecture guard tests: enforce inward dependency direction.

Layer dependency rules:
  core     → (no project imports)
  domain   → core only
  application → domain, core
  infrastructure → application, domain, core
  presentation → infrastructure, application, domain, core
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import cast

import pytest

_SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "aerobim"
sys.path.insert(0, str(_SRC_ROOT.parent))

_LAYER_ORDER = ["core", "domain", "application", "infrastructure", "presentation"]

_ALLOWED_IMPORTS: dict[str, set[str]] = {
    "core": set(),
    "domain": {"core"},
    "application": {"core", "domain"},
    "infrastructure": {"core", "domain", "application"},
    "presentation": {"core", "domain", "application", "infrastructure"},
}


def _layer_of(module_name: str) -> str | None:
    """Return layer name if module is inside aerobim.<layer>, else None."""
    parts = module_name.split(".")
    if len(parts) >= 2 and parts[0] == "aerobim" and parts[1] in _LAYER_ORDER:
        return parts[1]
    return None


def _collect_python_files(layer: str) -> list[Path]:
    layer_dir = _SRC_ROOT / layer
    if not layer_dir.is_dir():
        return []
    return sorted(layer_dir.rglob("*.py"))


def _extract_imports(filepath: Path) -> list[str]:
    """Extract all import targets from a Python source file."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _build_violation_cases() -> list[tuple[str, str, str, str]]:
    """Return (layer, filepath, imported_module, violated_layer) tuples."""
    violations: list[tuple[str, str, str, str]] = []
    for layer in _LAYER_ORDER:
        allowed = _ALLOWED_IMPORTS[layer]
        for filepath in _collect_python_files(layer):
            for imported in _extract_imports(filepath):
                imported_layer = _layer_of(imported)
                if imported_layer is None:
                    continue
                if imported_layer == layer:
                    continue
                if imported_layer not in allowed:
                    rel = filepath.relative_to(_SRC_ROOT.parent.parent)
                    violations.append((layer, str(rel), imported, imported_layer))
    return violations


_VIOLATIONS = _build_violation_cases()


@pytest.mark.parametrize(
    "layer,filepath,imported,violated_layer",
    _VIOLATIONS,
    ids=[f"{v[0]}:{Path(v[1]).name}→{v[3]}" for v in _VIOLATIONS] if _VIOLATIONS else ["no_violations"],
)
def test_no_layer_violations(layer: str, filepath: str, imported: str, violated_layer: str) -> None:
    pytest.fail(
        f"Layer violation: {layer}/{filepath} imports {imported} "
        f"({violated_layer} layer). {layer} may only import from {_ALLOWED_IMPORTS[layer]}."
    )


def test_no_violations_found() -> None:
    """Ensure the parametrize approach found zero violations (green baseline)."""
    assert _VIOLATIONS == [], f"Found {len(_VIOLATIONS)} layer violation(s): {_VIOLATIONS}"


def test_domain_does_not_import_infrastructure() -> None:
    """Explicit guard: domain must never touch infrastructure."""
    for filepath in _collect_python_files("domain"):
        for imported in _extract_imports(filepath):
            assert "infrastructure" not in imported, (
                f"Domain file {filepath.name} imports infrastructure module: {imported}"
            )


def test_domain_does_not_import_presentation() -> None:
    """Explicit guard: domain must never touch presentation."""
    for filepath in _collect_python_files("domain"):
        for imported in _extract_imports(filepath):
            assert "presentation" not in imported, (
                f"Domain file {filepath.name} imports presentation module: {imported}"
            )


def test_core_has_no_project_imports() -> None:
    """Core layer must not import any other aerobim layer."""
    for filepath in _collect_python_files("core"):
        for imported in _extract_imports(filepath):
            imported_layer = _layer_of(imported)
            if imported_layer is not None and imported_layer != "core":
                pytest.fail(
                    f"Core file {filepath.name} imports {imported} ({imported_layer} layer)"
                )


def test_all_di_tokens_registered() -> None:
    """Every token in Tokens class must be registered in bootstrap_container."""
    from aerobim.core.di.tokens import Tokens

    token_namespace = cast(dict[str, object], Tokens.__dict__)
    token_values = {
        v for k, v in token_namespace.items() if not k.startswith("_") and isinstance(v, str)
    }

    bootstrap_path = _SRC_ROOT / "infrastructure" / "di" / "bootstrap.py"
    bootstrap_src = bootstrap_path.read_text(encoding="utf-8")

    for token in token_values:
        assert f'Tokens.{token.upper().replace(" ", "_")}' in bootstrap_src or token in bootstrap_src, (
            f"Token '{token}' not found in bootstrap.py"
        )
