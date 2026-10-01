"""P-001 isolation guard: copyleft / dual-commercial dependencies must stay behind
the infrastructure/tools seam.

VERIFIED baseline 2026-07-31: pymupdf (AGPL/commercial dual, LIC-001) and
ifcopenshell/ifctester (LGPL-3.0+) are imported ONLY from
``infrastructure/adapters`` and ``tools``. domain / application / presentation /
core never touch them, so a future backend migration (or commercial licensing
decision) has a contained swap surface. This guard keeps that surface contained.
"""

from __future__ import annotations

import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "aerobim"
_RESTRICTED = ("pymupdf", "ifcopenshell", "ifctester")
_IMPORT_RE = re.compile(r"(?:^|\s)(?:import|from)\s+(" + "|".join(_RESTRICTED) + r")\b")
# Layers allowed to touch restricted third-party engines.
_ALLOWED_PREFIXES = ("infrastructure/adapters/", "tools/")


def _violations() -> list[str]:
    found: list[str] = []
    for path in sorted(_SRC.rglob("*.py")):
        rel = path.relative_to(_SRC).as_posix()
        if rel.startswith(_ALLOWED_PREFIXES):
            continue
        text = path.read_text(encoding="utf-8")
        for match in _IMPORT_RE.finditer(text):
            found.append(f"{rel}: imports {match.group(1)}")
    return found


def test_copyleft_engines_stay_behind_infrastructure_seam() -> None:
    violations = _violations()
    assert not violations, (
        "Copyleft/dual-commercial imports leaked outside infrastructure/tools "
        "(this widens the LIC-001 migration surface):\n" + "\n".join(violations)
    )


def test_guard_actually_scans_known_users() -> None:
    # Not tautological: the allowed layers DO use the engines today.
    used = [
        path
        for path in _SRC.rglob("*.py")
        if path.relative_to(_SRC).as_posix().startswith(_ALLOWED_PREFIXES)
        and _IMPORT_RE.search(path.read_text(encoding="utf-8"))
    ]
    assert used, "expected at least one adapter/tool importing a restricted engine"


def test_runtime_lock_excludes_optional_pymupdf() -> None:
    lock = Path(__file__).resolve().parents[1] / "requirements-lock.txt"
    for line in lock.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().lower().rstrip("\\").strip()
        assert not stripped.startswith("pymupdf==") and not stripped.startswith("pymupdf["), (
            "pymupdf must stay behind extra pdf-agpl; runtime lock must not install it"
        )
