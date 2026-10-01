#!/usr/bin/env python3
"""Verify governance/ruff_s_band_inventory.json matches pyproject.toml per-file-ignores."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    root = _repo_root()
    inventory_path = root / "governance/ruff_s_band_inventory.json"
    pyproject_path = root / "backend/pyproject.toml"

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    ignores = pyproject["tool"]["ruff"]["lint"]["per-file-ignores"]

    inv_map = {entry["glob"]: set(entry["rules"]) for entry in inventory["entries"]}
    py_map = {glob: set(rules) for glob, rules in ignores.items()}

    errors: list[str] = []
    only_inventory = sorted(set(inv_map) - set(py_map))
    only_pyproject = sorted(set(py_map) - set(inv_map))
    if only_inventory:
        errors.append(f"globs only in inventory: {only_inventory}")
    if only_pyproject:
        errors.append(f"globs only in pyproject.toml: {only_pyproject}")

    for glob in sorted(set(inv_map) & set(py_map)):
        if inv_map[glob] != py_map[glob]:
            errors.append(
                f"{glob}: inventory={sorted(inv_map[glob])} "
                f"pyproject={sorted(py_map[glob])}"
            )

    if errors:
        for line in errors:
            print(f"ERROR: {line}", file=sys.stderr)
        return 1

    print(f"ruff S-band inventory OK ({len(inv_map)} globs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
