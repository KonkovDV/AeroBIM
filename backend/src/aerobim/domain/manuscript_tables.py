"""Manuscript cells copied only from attested evidence pins.

A cell is citable when the pin has ``attested_by`` equal to ``ci`` and a
non-empty ``claim_level``. Anything else is withheld: the number stays in
the pin and is not repeated in the table. This is not a product-accuracy
claim and it does not set ``summary.passed``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_FORBIDDEN_CLAIM_LEVELS: Final[frozenset[str]] = frozenset(
    {
        "product_accuracy",
        "customer_accuracy",
        "cde_ready",
    }
)


@dataclass(frozen=True, slots=True)
class ManuscriptSpec:
    """One cell: section, label, pin path relative to the repo, JSON pointer."""

    section: str
    label: str
    pin: str
    pointer: str


@dataclass(frozen=True, slots=True)
class ManuscriptCell:
    spec: ManuscriptSpec
    citable: bool
    value: object | None
    reason: str


# Pointers only. Values are read from the pin at render time.
MANUSCRIPT_SPECS: Final[tuple[ManuscriptSpec, ...]] = (
    ManuscriptSpec(
        "Architecture",
        "Backend tests passed",
        "docs/evidence/runtime-baseline-latest.json",
        "backend.tests_passed",
    ),
    ManuscriptSpec(
        "Architecture",
        "Backend tests collected",
        "docs/evidence/runtime-baseline-latest.json",
        "backend.tests_collected",
    ),
    ManuscriptSpec(
        "Architecture",
        "Backend tests failed",
        "docs/evidence/runtime-baseline-latest.json",
        "backend.tests_failed",
    ),
    ManuscriptSpec(
        "Architecture",
        "Frontend tests passed",
        "docs/evidence/runtime-baseline-latest.json",
        "frontend.tests_passed",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Dual-rater rehearsal n",
        "docs/evidence/rt001-dual-rater-simulation-2026-09.json",
        "n",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Dual-rater rehearsal Cohen kappa",
        "docs/evidence/rt001-dual-rater-simulation-2026-09.json",
        "cohens_kappa",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Dual-rater rehearsal Gwet AC1",
        "docs/evidence/rt001-dual-rater-simulation-2026-09.json",
        "gwet_ac1",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Independent human raters",
        "docs/evidence/rt001-dual-rater-simulation-2026-09.json",
        "independent_human_raters",
    ),
    ManuscriptSpec(
        "Evaluation",
        "IFC-Bench v1 scored questions",
        "docs/evidence/ifc-bench-v1-smoke-latest.json",
        "summary.scored",
    ),
    ManuscriptSpec(
        "Evaluation",
        "IFC-Bench v1 question count",
        "docs/evidence/ifc-bench-v1-smoke-latest.json",
        "summary.total_questions",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Mutation-kill trials",
        "docs/evidence/defect-injection-recall-run-fixture-latest.json",
        "aggregate.trials",
    ),
    ManuscriptSpec(
        "Evaluation",
        "Mutation-kill successes",
        "docs/evidence/defect-injection-recall-run-fixture-latest.json",
        "aggregate.killed",
    ),
)


def load_pin(path: Path) -> dict[str, object]:
    """Load a pin. A leading claims-lint comment is ignored."""

    text = path.read_text(encoding="utf-8")
    start = text.find("{")
    if start < 0:
        raise ValueError(f"{path} has no JSON object")
    payload = json.loads(text[start:])
    if not isinstance(payload, dict):
        raise ValueError(f"{path} JSON root is not an object")
    return payload


def cite_gate(pin: Mapping[str, object]) -> tuple[bool, str]:
    """Return whether the pin may be copied into a manuscript cell."""

    attested = _attested_by(pin)
    level = pin.get("claim_level")
    if attested != "ci":
        return False, f"attested_by is {attested!r}, need ci"
    if not isinstance(level, str) or not level.strip():
        return False, "claim_level missing"
    if level in _FORBIDDEN_CLAIM_LEVELS:
        return False, f"claim_level {level!r} is not citable"
    return True, ""


def manuscript_cells(
    repo: Path, specs: Sequence[ManuscriptSpec] = MANUSCRIPT_SPECS
) -> tuple[ManuscriptCell, ...]:
    """Read each spec. Withheld cells keep ``value`` None."""

    cells: list[ManuscriptCell] = []
    for spec in specs:
        path = repo / spec.pin
        if not path.is_file():
            cells.append(ManuscriptCell(spec, False, None, "pin file missing"))
            continue
        try:
            pin = load_pin(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            cells.append(ManuscriptCell(spec, False, None, f"pin unreadable: {exc}"))
            continue
        allowed, reason = cite_gate(pin)
        if not allowed:
            cells.append(ManuscriptCell(spec, False, None, reason))
            continue
        found, value = _lookup(pin, spec.pointer)
        if not found:
            cells.append(ManuscriptCell(spec, False, None, "pointer missing"))
            continue
        if not _is_scalar(value):
            cells.append(ManuscriptCell(spec, False, None, "value is not a scalar"))
            continue
        cells.append(ManuscriptCell(spec, True, value, ""))
    return tuple(cells)


def render_manuscript_markdown(cells: Sequence[ManuscriptCell]) -> str:
    """Markdown for Architecture and Evaluation. Withheld numbers are omitted."""

    lines = [
        "# Manuscript tables",
        "",
        "A cell is printed only when its pin has `attested_by` = `ci` and a",
        "non-empty `claim_level`. Other cells stay withheld. This is not product",
        "accuracy and it does not set `customer_go`.",
        "",
    ]
    for section in ("Architecture", "Evaluation"):
        lines.append(f"## {section}")
        lines.append("")
        lines.append("| Label | Pin | Pointer | Value |")
        lines.append("|---|---|---|---|")
        for cell in cells:
            if cell.spec.section != section:
                continue
            value = "withheld" if not cell.citable else _format_scalar(cell.value)
            lines.append(
                f"| {cell.spec.label} | `{cell.spec.pin}` | `{cell.spec.pointer}` | {value} |"
            )
        lines.append("")
    lines.append("## Withheld")
    lines.append("")
    lines.append("| Label | Reason |")
    lines.append("|---|---|")
    for cell in cells:
        if cell.citable:
            continue
        lines.append(f"| {cell.spec.label} | {cell.reason} |")
    lines.append("")
    return "\n".join(lines)


def _attested_by(pin: Mapping[str, object]) -> str | None:
    top = pin.get("attested_by")
    if isinstance(top, str):
        return top
    attestation = pin.get("attestation")
    if isinstance(attestation, Mapping):
        nested = attestation.get("attested_by")
        if isinstance(nested, str):
            return nested
    return None


def _lookup(pin: Mapping[str, object], pointer: str) -> tuple[bool, object]:
    current: object = pin
    for part in pointer.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _format_scalar(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)
