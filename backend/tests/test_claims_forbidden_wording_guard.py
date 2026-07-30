"""TR-401 guard: forbidden claim phrases (SSOT:
audit/claims_forbidden_wording.json) may appear in public docs only inside a
negation/honesty context, so a marketing edit cannot silently drift into a
forbidden affirmative claim (Red Team attack A1)."""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SSOT = _REPO_ROOT / "audit" / "claims_forbidden_wording.json"


def _string_list(value: object) -> list[str]:
    assert isinstance(value, list)
    return [str(item) for item in value]


def _load_ssot() -> dict[str, object]:
    data = json.loads(_SSOT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_ssot_present_and_populated() -> None:
    ssot = _load_ssot()
    assert _string_list(ssot["forbidden_affirmative_phrases"])
    assert _string_list(ssot["negation_markers"])
    assert _string_list(ssot["scanned_files"])


def test_forbidden_phrases_only_in_negation_context() -> None:
    ssot = _load_ssot()
    phrases = [p.lower() for p in _string_list(ssot["forbidden_affirmative_phrases"])]
    markers = [m.lower() for m in _string_list(ssot["negation_markers"])]
    violations: list[str] = []
    for rel in _string_list(ssot["scanned_files"]):
        path = _REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        for lineno, raw in enumerate(text.splitlines(), start=1):
            line = raw.lower()
            for phrase in phrases:
                if phrase in line and not any(marker in line for marker in markers):
                    violations.append(f"{rel}:{lineno}: forbidden affirmative claim {phrase!r}")
    assert not violations, "Claims drift (negate the line or remove the claim):\n" + "\n".join(
        violations
    )
