"""TR-401 guard: forbidden claim phrases (SSOT:
audit/claims_forbidden_wording.json) may appear in public docs only inside a
negation/honesty context, so a marketing edit cannot silently drift into a
forbidden affirmative claim (Red Team attack A1)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SSOT = _REPO_ROOT / "audit" / "claims_forbidden_wording.json"
# Strip inline Markdown (emphasis/code/link markup) so a forbidden phrase cannot
# hide as e.g. `production-**ready**` and slip past the substring guard (RT-1).
_MARKDOWN_MARKUP = re.compile(r"[*_`~\[\]()]")


def _string_list(value: object) -> list[str]:
    assert isinstance(value, list)
    return [str(item) for item in value]


def _load_ssot() -> dict[str, object]:
    data = json.loads(_SSOT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _negation_coverage():
    scripts = str(_REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from lint_claims import negation_coverage  # type: ignore[import-not-found]

    return negation_coverage


def test_ssot_present_and_populated() -> None:
    ssot = _load_ssot()
    assert _string_list(ssot["forbidden_affirmative_phrases"])
    assert _string_list(ssot["negation_markers"])
    assert _string_list(ssot["scanned_files"])


def test_forbidden_phrases_only_in_negation_context() -> None:
    ssot = _load_ssot()
    phrases = [p.lower() for p in _string_list(ssot["forbidden_affirmative_phrases"])]
    markers = [m.lower() for m in _string_list(ssot["negation_markers"])]
    coverage_fn = _negation_coverage()
    violations: list[str] = []
    for rel in _string_list(ssot["scanned_files"]):
        path = _REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        inherited = coverage_fn(lines, markers)
        for lineno, raw in enumerate(lines, start=1):
            if inherited[lineno - 1]:
                continue
            line = _MARKDOWN_MARKUP.sub("", raw.lower())
            for phrase in phrases:
                if phrase in line:
                    violations.append(f"{rel}:{lineno}: forbidden affirmative claim {phrase!r}")
    assert not violations, "Claims drift (negate the line or remove the claim):\n" + "\n".join(
        violations
    )


def test_markdown_obfuscated_phrase_is_still_caught() -> None:
    # RT-1: markup must not let a forbidden affirmative claim slip past the guard.
    markers = [m.lower() for m in _string_list(_load_ssot()["negation_markers"])]
    normalized = _MARKDOWN_MARKUP.sub("", "AeroBIM is production-**ready** today".lower())
    assert "production-ready" in normalized
    assert not any(marker in normalized for marker in markers)


def test_planned_and_never_are_not_bare_negation_markers() -> None:
    # RT-2: overly permissive bare markers removed so an affirmative claim cannot ride them.
    markers = [m.lower() for m in _string_list(_load_ssot()["negation_markers"])]
    assert "planned" not in markers
    assert "never" not in markers


def test_ssot_covers_ru_markers_and_core_surfaces() -> None:
    ssot = _load_ssot()
    markers = [m.lower() for m in _string_list(ssot["negation_markers"])]
    scanned = _string_list(ssot["scanned_files"])
    for marker in ("запрещено", "нельзя", "не заявляется", "до доказательств"):
        assert marker in markers
    for rel in (
        "README.md",
        "README.ru.md",
        "docs/TIER0_INDEX.md",
        "docs/ENGINEERING_STATUS_2026_08.md",
        "docs/docs.md",
        "docs/demo/KT2_JURY_FAQ_2026_08_12.md",
        "docs/pilot-claim-boundary-2026.md",
        "submission/README.md",
        "submission/01-repository/README.md",
        "submission/02-documentation/README.md",
        "submission/03-presentation/README.md",
        "submission/03-presentation/slides.md",
        "submission/04-prototype/README.md",
        "submission/05-additional/README.md",
        "submission/TZ_REQUIREMENTS_COVERAGE_2026_08.md",
    ):
        assert rel in scanned


def test_heading_negation_covers_following_list_items() -> None:
    """HDS-SUB-02: 'Запрещено' heading covers the following list run."""
    coverage = _negation_coverage()(
        [
            "## Запрещено в кадре",
            "",
            "- MEP delivered",
            "- CDE-ready",
        ],
        ["запрещено", "not claimed"],
    )
    assert coverage[2] and coverage[3]


def test_nelzya_heading_covers_following_list_items() -> None:
    coverage = _negation_coverage()(
        [
            "## Нельзя говорить",
            "",
            "- SLA ≤30",
            "- Checkpoint GO",
        ],
        ["нельзя", "запрещено", "not claimed"],
    )
    assert coverage[2] and coverage[3]


def test_list_item_negation_carries_across_blank_lines() -> None:
    coverage = _negation_coverage()(
        [
            "- Not claimed: production-ready",
            "",
            "- CDE-ready",
        ],
        ["not claimed", "forbidden"],
    )
    assert coverage[0] and coverage[2]


def test_new_heading_resets_inherited_negation() -> None:
    coverage = _negation_coverage()(
        [
            "## Forbidden slogans",
            "- production-ready",
            "## Status",
            "- production-ready",
        ],
        ["forbidden", "not claimed"],
    )
    assert coverage[1]
    assert not coverage[3]
