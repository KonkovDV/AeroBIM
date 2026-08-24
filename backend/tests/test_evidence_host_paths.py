"""Committed evidence must not leak retired host checkout paths (C:\\plans)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ROOTS = (
    REPO / "docs" / "evidence",
    REPO / "audit" / "evidence",
)
_HOST_RE = re.compile(r"(?i)C:[/\\]+plans")


def test_evidence_json_has_no_c_plans_checkout_paths() -> None:
    leaked: list[str] = []
    for root in EVIDENCE_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*.json"):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if _HOST_RE.search(text):
                leaked.append(path.relative_to(REPO).as_posix())
    assert leaked == [], f"host checkout paths in evidence JSON: {leaked}"
