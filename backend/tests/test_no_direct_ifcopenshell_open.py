"""Lint: every IFC open goes through ``aerobim.infrastructure.adapters.ifc_file_open``.

Direct ``ifcopenshell.open`` bypasses the pre-final IFC4x3 → IFC4X3_ADD2
fallback, the lost-instance check and the size policy. Use ``open_ifc_file``
(uncached) or ``open_ifc_model`` / ``open_ifc_session`` (cached) instead.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (REPO / "backend" / "src", REPO / "backend" / "tests", REPO / "scripts")
HELPER = REPO / "backend" / "src" / "aerobim" / "infrastructure" / "adapters" / "ifc_file_open.py"


def direct_open_calls(source: str) -> list[int]:
    """Line numbers of ``ifcopenshell.open(...)`` or ``from ifcopenshell import open``."""

    tree = ast.parse(source)
    module_aliases = {"ifcopenshell"}
    open_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "ifcopenshell" and alias.asname:
                    module_aliases.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module == "ifcopenshell":
            for alias in node.names:
                if alias.name == "open":
                    open_aliases.add(alias.asname or "open")
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "ifcopenshell":
            if any(alias.name == "open" for alias in node.names):
                hits.append(node.lineno)
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "open"
            and isinstance(func.value, ast.Name)
            and func.value.id in module_aliases
        ):
            hits.append(node.lineno)
        elif isinstance(func, ast.Name) and func.id in open_aliases:
            hits.append(node.lineno)
    return sorted(set(hits))


class NoDirectIfcopenshellOpenTests(unittest.TestCase):
    def test_detector_catches_known_spellings(self) -> None:
        self.assertEqual(direct_open_calls("import ifcopenshell\nifcopenshell.open('a')\n"), [2])
        self.assertEqual(direct_open_calls("import ifcopenshell as ios\nios.open('a')\n"), [2])
        self.assertEqual(direct_open_calls("from ifcopenshell import open as o\no('a')\n"), [1, 2])
        self.assertEqual(direct_open_calls("import ifctester\nifctester.open('x.ids')\n"), [])
        self.assertEqual(direct_open_calls("open('plain.txt')\n"), [])

    def test_no_direct_open_outside_helper(self) -> None:
        offenders: list[str] = []
        for root in SCAN_ROOTS:
            for path in sorted(root.rglob("*.py")):
                if path.resolve() == HELPER.resolve() or "__pycache__" in path.parts:
                    continue
                for line in direct_open_calls(path.read_text(encoding="utf-8")):
                    offenders.append(f"{path.relative_to(REPO).as_posix()}:{line}")
        self.assertEqual(
            offenders,
            [],
            "use aerobim.infrastructure.adapters.ifc_file_open.open_ifc_file "
            "instead of ifcopenshell.open",
        )


if __name__ == "__main__":
    unittest.main()
