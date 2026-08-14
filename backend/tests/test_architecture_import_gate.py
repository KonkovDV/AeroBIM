"""Architecture layer-import gate (RT-20260811-04).

Enforces Clean Architecture import direction on production packages:

    core ↛ domain/application/infrastructure/presentation/tools
    domain ↛ application/infrastructure/presentation/tools
    application ↛ infrastructure/presentation/tools

Infrastructure and presentation may import inward. Tools/main are composition
edges and are not scanned as layers here.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "aerobim"

_FORBIDDEN: dict[str, frozenset[str]] = {
    "core": frozenset(
        {
            "aerobim.domain",
            "aerobim.application",
            "aerobim.infrastructure",
            "aerobim.presentation",
            "aerobim.tools",
            "aerobim.main",
        }
    ),
    "domain": frozenset(
        {
            "aerobim.application",
            "aerobim.infrastructure",
            "aerobim.presentation",
            "aerobim.tools",
            "aerobim.main",
        }
    ),
    "application": frozenset(
        {
            "aerobim.infrastructure",
            "aerobim.presentation",
            "aerobim.tools",
            "aerobim.main",
        }
    ),
}


def _iter_imported_modules(
    tree: ast.AST, *, module_file: Path, layer: str
) -> list[tuple[str, int]]:
    """Return (absolute-ish module name, lineno) for Import / ImportFrom nodes."""

    package_parts = ("aerobim", layer, *module_file.parent.relative_to(_SRC_ROOT / layer).parts)
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None and (node.level or 0) == 0:
                continue
            if node.level:
                # Resolve relative import against this file's package.
                base = list(package_parts[: len(package_parts) - (node.level - 1)])
                if node.module:
                    abs_mod = ".".join([*base, *node.module.split(".")])
                else:
                    abs_mod = ".".join(base)
            else:
                abs_mod = node.module or ""
            if abs_mod:
                found.append((abs_mod, node.lineno))
    return found


def _violations_for_layer(layer: str) -> list[str]:
    layer_root = _SRC_ROOT / layer
    forbidden = _FORBIDDEN[layer]
    violations: list[str] = []
    for path in sorted(layer_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for mod, lineno in _iter_imported_modules(tree, module_file=path, layer=layer):
            for bad in forbidden:
                if mod == bad or mod.startswith(f"{bad}."):
                    rel = path.relative_to(_SRC_ROOT.parents[1]).as_posix()
                    violations.append(f"{rel}:{lineno} imports {mod} (forbidden from {layer})")
    return violations


class ArchitectureImportGateTests(unittest.TestCase):
    def test_core_domain_application_import_direction(self) -> None:
        violations: list[str] = []
        for layer in ("core", "domain", "application"):
            violations.extend(_violations_for_layer(layer))
        if violations:
            self.fail("Clean Architecture import violations:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
