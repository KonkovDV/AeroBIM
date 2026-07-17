"""Load-table numeric сверка from calculation sources (not correctness)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue, ValidationRequest
from aerobim.domain.quantity import parse_quantity, si_compare

_LOAD_ROW = re.compile(
    r"(?P<id>[A-Za-zА-Яа-я0-9_.\-]+)\s*[|;]\s*"
    r"(?P<label>[^|;]+)\s*[|;]\s*"
    r"(?P<expected>-?\d+(?:[.,]\d+)?)\s*[|;]\s*"
    r"(?P<unit>[A-Za-zА-Яа-я²³23/]*)\s*[|;]\s*"
    r"(?P<observed>-?\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


def _numeric_match(expected: float, observed: float, unit: str) -> bool:
    q_e = parse_quantity(expected, unit or "kN")
    q_o = parse_quantity(observed, unit or "kN")
    if q_e.si_value is not None and q_o.si_value is not None:
        return si_compare(q_e, q_o, epsilon=1e-3)
    return abs(expected - observed) <= 1e-3


class SpreadsheetLoadEvidenceAdapter:
    """Parse calculation_source for LOAD|id|label|expected|unit|observed rows or JSON."""

    def verify(self, request: ValidationRequest) -> list[ValidationIssue]:
        source = request.calculation_source
        if source is None:
            return []

        conflict_issues: list[ValidationIssue] = []
        text = ""
        source_id = source.source_id or "calculation"

        # RT-CALC-005: .json path is SSOT when present (text must not shadow).
        if source.path is not None and source.path.suffix.lower() == ".json":
            text = self._load_path(source.path)
            inline = source.text.strip()
            if inline and inline != text.strip():
                conflict_issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-FORMAT",
                        severity=Severity.WARNING,
                        message=(
                            "Calculation source text disagrees with .json path; "
                            "path is SSOT — load OK suppressed"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id=source_id,
                    )
                )
        else:
            text = source.text.strip()
            if not text and source.path is not None:
                text = self._load_path(source.path)

        if not text.strip():
            return [
                ValidationIssue(
                    rule_id="AEROBIM-LOAD-FORMAT",
                    severity=Severity.INFO,
                    message="Calculation source empty; no LOAD rows evaluated",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=source_id,
                )
            ]

        if text.lstrip().startswith("{"):
            issues = self._verify_json(text, source_id=source_id)
        else:
            issues = self._verify_tabular(text, source_id=source_id)

        if conflict_issues:
            issues = [item for item in issues if item.rule_id != "AEROBIM-LOAD-OK"]
            return [*conflict_issues, *issues]
        return issues

    def _load_path(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8")

    def _verify_json(self, text: str, *, source_id: str) -> list[ValidationIssue]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-LOAD-JSON",
                    severity=Severity.WARNING,
                    message=f"Calculation JSON parse failed: {exc}",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=source_id,
                )
            ]
        rows = payload.get("loads") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            return [
                ValidationIssue(
                    rule_id="AEROBIM-LOAD-SCHEMA",
                    severity=Severity.INFO,
                    message="Calculation JSON has no 'loads' array; load сверка skipped",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=source_id,
                )
            ]
        issues: list[ValidationIssue] = []
        evaluated_ok = 0
        if len(rows) == 0:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-LOAD-FORMAT",
                    severity=Severity.INFO,
                    message="Calculation JSON 'loads' array is empty; no rows evaluated",
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=source_id,
                )
            ]
        for index, row in enumerate(rows):
            # RT-CALC-004: never silently skip non-dict rows.
            if not isinstance(row, dict):
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-ROW",
                        severity=Severity.WARNING,
                        message=f"loads[{index}] is not an object",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id=source_id,
                    )
                )
                continue
            load_id = str(row.get("id", "load"))
            unit = str(row.get("unit", "") or "")
            try:
                expected = float(row["expected"])
                observed = float(row["observed"])
            except (KeyError, TypeError, ValueError):
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-ROW",
                        severity=Severity.WARNING,
                        message=f"Load row {load_id} missing expected/observed numerics",
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=load_id,
                        source_id=source_id,
                    )
                )
                continue
            if not _numeric_match(expected, observed, unit):
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-MISMATCH",
                        severity=Severity.WARNING,
                        message=(
                            f"Load match failed for {load_id}: "
                            f"expected={expected} observed={observed} {unit}"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=load_id,
                        expected_value=str(expected),
                        observed_value=str(observed),
                        unit=unit or None,
                        source_id=source_id,
                    )
                )
            else:
                evaluated_ok += 1
        if any(i.rule_id == "AEROBIM-LOAD-MISMATCH" for i in issues):
            return issues
        if any(i.rule_id == "AEROBIM-LOAD-ROW" for i in issues):
            return issues
        if evaluated_ok == 0:
            if not issues:
                return [
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-FORMAT",
                        severity=Severity.INFO,
                        message="Calculation JSON loads present but no numeric rows evaluated",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id=source_id,
                    )
                ]
            return issues
        return [
            ValidationIssue(
                rule_id="AEROBIM-LOAD-OK",
                severity=Severity.INFO,
                message=f"Load сверка matched {evaluated_ok} row(s) (not correctness)",
                category=FindingCategory.CROSS_DOCUMENT,
                source_id=source_id,
            ),
            *issues,
        ]

    def _verify_tabular(self, text: str, *, source_id: str) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        matched_any = False
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.upper().startswith("LOAD|") or stripped.upper().startswith("LOAD;"):
                stripped = (
                    stripped.split("|", 1)[-1] if "|" in stripped else stripped.split(";", 1)[-1]
                )
            match = _LOAD_ROW.search(stripped)
            if match is None:
                continue
            matched_any = True
            expected = float(match.group("expected").replace(",", "."))
            observed = float(match.group("observed").replace(",", "."))
            unit = (match.group("unit") or "").strip()
            load_id = match.group("id").strip()
            if not _numeric_match(expected, observed, unit):
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-MISMATCH",
                        severity=Severity.WARNING,
                        message=(
                            f"Load match failed for {load_id}: "
                            f"expected={expected} observed={observed} {unit}"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        target_ref=load_id,
                        expected_value=str(expected),
                        observed_value=str(observed),
                        unit=unit or None,
                        source_id=source_id,
                    )
                )
        if not matched_any:
            return [
                ValidationIssue(
                    rule_id="AEROBIM-LOAD-FORMAT",
                    severity=Severity.INFO,
                    message=(
                        "Calculation source present but no LOAD rows matched; "
                        "expected LOAD|id|label|expected|unit|observed"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id=source_id,
                )
            ]
        if any(i.rule_id == "AEROBIM-LOAD-MISMATCH" for i in issues):
            return issues
        return [
            ValidationIssue(
                rule_id="AEROBIM-LOAD-OK",
                severity=Severity.INFO,
                message="Load сверка matched tabular row(s) (not correctness)",
                category=FindingCategory.CROSS_DOCUMENT,
                source_id=source_id,
            ),
            *issues,
        ]
