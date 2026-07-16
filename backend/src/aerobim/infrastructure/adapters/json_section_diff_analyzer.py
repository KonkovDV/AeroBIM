"""Deterministic JSON scaffold for one discipline-specific PD/RD section pair.

Matching is performed on **canonical keys** and **canonical discipline codes**
(see :mod:`aerobim.domain.section_pairing`) so RU/EN aliases pair up without any
fuzzy, OCR, CV, or model-generated matching. Comparison remains SI-normalised
and tolerance-banded; unresolved units are surfaced as ``UNIT_MISMATCH`` rather
than silently treated as equal.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.models import (
    ComparisonOperator,
    ConflictKind,
    FindingCategory,
    ProblemZone,
    Severity,
    ToleranceConfig,
    ValidationIssue,
)
from aerobim.domain.quantity import QuantityValue, parse_quantity
from aerobim.domain.section_pairing import (
    DisciplineInfo,
    SectionPairingReport,
    canonicalize_discipline,
    canonicalize_key,
    slugify,
)

_MAX_SECTION_BYTES = 2 * 1024 * 1024
_MAX_VALUES = 2_000
_KEY_RE = re.compile(r"^[\w.:/-]{1,256}$", re.UNICODE)

_PD_STAGE_ALIASES = {"PD", "ПД"}
_RD_STAGE_ALIASES = {"RD", "РД"}


@dataclass(frozen=True)
class _SectionValue:
    key: str
    canonical_key: str
    key_recognized: bool
    value: str
    unit: str | None
    target_ref: str | None
    source_ref: str | None
    problem_zone: ProblemZone | None
    required_in_rd: bool
    tolerance_si: float | None


@dataclass(frozen=True)
class _SectionDocument:
    document_id: str
    project_id: str
    stage: str
    discipline: str
    discipline_info: DisciplineInfo
    section_code: str
    revision: str
    basis_document_id: str | None
    basis_revision: str | None
    values: tuple[_SectionValue, ...]


class JsonSectionDiffAnalyzer:
    """Compare normalized section evidence without fuzzy or model-generated matching."""

    def __init__(
        self,
        *,
        tolerance: ToleranceConfig | None = None,
        severity: Severity = Severity.WARNING,
    ) -> None:
        self._tolerance = tolerance or ToleranceConfig()
        self._severity = severity

    def compare(self, pd_section_path: Path, rd_section_path: Path) -> list[ValidationIssue]:
        """Return findings only (minimal port contract, delegates to ``analyze``)."""
        return list(self.analyze(pd_section_path, rd_section_path).issues)

    def analyze(self, pd_section_path: Path, rd_section_path: Path) -> SectionPairingReport:
        pd = self._load(pd_section_path)
        rd = self._load(rd_section_path)
        if pd.stage not in _PD_STAGE_ALIASES:
            raise ValueError(
                f"PD section input {pd.document_id!r} has stage {pd.stage!r}; expected PD/ПД"
            )
        if rd.stage not in _RD_STAGE_ALIASES:
            raise ValueError(
                f"RD section input {rd.document_id!r} has stage {rd.stage!r}; expected RD/РД"
            )
        if pd.project_id != rd.project_id:
            raise ValueError(
                f"PD/RD section project_id mismatch: {pd.project_id!r} != {rd.project_id!r}"
            )

        issues = self._metadata_issues(pd, rd)
        rd_by_key = {item.canonical_key: item for item in rd.values}
        for expected in pd.values:
            observed = rd_by_key.get(expected.canonical_key)
            if observed is None:
                if expected.required_in_rd:
                    issues.append(self._missing_issue(pd, rd, expected))
                continue
            conflict_kind = self._classify_value_conflict(expected, observed)
            if conflict_kind is not None:
                issues.append(self._value_issue(pd, rd, expected, observed, conflict_kind))

        recognized = sum(1 for value in pd.values if value.key_recognized)
        unrecognized = tuple(value.key for value in pd.values if not value.key_recognized)
        return SectionPairingReport(
            issues=tuple(issues),
            discipline=pd.discipline_info,
            section_code=pd.section_code,
            pd_document_id=pd.document_id,
            rd_document_id=rd.document_id,
            pd_key_count=len(pd.values),
            recognized_key_count=recognized,
            unrecognized_keys=unrecognized,
        )

    def _metadata_issues(
        self,
        pd: _SectionDocument,
        rd: _SectionDocument,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if pd.discipline_info.code != rd.discipline_info.code:
            issues.append(
                self._metadata_issue(
                    pd,
                    rd,
                    "DISCIPLINE",
                    "discipline",
                    pd.discipline,
                    rd.discipline,
                    ConflictKind.STAGE_MISMATCH,
                )
            )
        if pd.section_code != rd.section_code:
            issues.append(
                self._metadata_issue(
                    pd,
                    rd,
                    "SECTION-CODE",
                    "section_code",
                    pd.section_code,
                    rd.section_code,
                    ConflictKind.STAGE_MISMATCH,
                )
            )
        if rd.basis_document_id and rd.basis_document_id != pd.document_id:
            issues.append(
                self._metadata_issue(
                    pd,
                    rd,
                    "BASIS-DOCUMENT",
                    "basis.document_id",
                    pd.document_id,
                    rd.basis_document_id,
                    ConflictKind.VERSION_MISMATCH,
                )
            )
        if rd.basis_revision and rd.basis_revision != pd.revision:
            issues.append(
                self._metadata_issue(
                    pd,
                    rd,
                    "BASIS-REVISION",
                    "basis.revision",
                    pd.revision,
                    rd.basis_revision,
                    ConflictKind.VERSION_MISMATCH,
                )
            )
        return issues

    def _metadata_issue(
        self,
        pd: _SectionDocument,
        rd: _SectionDocument,
        suffix: str,
        key: str,
        expected: str,
        observed: str,
        kind: ConflictKind,
    ) -> ValidationIssue:
        return ValidationIssue(
            rule_id=f"SECTION-PAIR-{slugify(pd.section_code)}-{suffix}",
            severity=self._severity,
            message=(
                f"PD/RD section metadata mismatch for {key}: PD={expected!r}, RD={observed!r}"
            ),
            category=FindingCategory.CROSS_DOCUMENT,
            target_ref=key,
            operator=ComparisonOperator.EQUALS,
            expected_value=expected,
            observed_value=observed,
            conflict_kind=kind,
            source_id=self._source_id(pd, rd),
            evidence_modality="section-pairing",
            confidence=1.0,
        )

    def _missing_issue(
        self,
        pd: _SectionDocument,
        rd: _SectionDocument,
        expected: _SectionValue,
    ) -> ValidationIssue:
        return ValidationIssue(
            rule_id=f"SECTION-PAIR-{slugify(pd.section_code)}-{slugify(expected.canonical_key)}",
            severity=self._severity,
            message=f"Required PD value {expected.key!r} is missing from paired RD section",
            category=FindingCategory.CROSS_DOCUMENT,
            target_ref=expected.target_ref or expected.key,
            operator=ComparisonOperator.EXISTS,
            expected_value=self._display_value(expected),
            observed_value=None,
            unit=expected.unit,
            problem_zone=expected.problem_zone,
            conflict_kind=ConflictKind.STAGE_MISMATCH,
            source_id=self._source_id(pd, rd),
            evidence_modality="section-pairing",
            confidence=1.0,
        )

    def _value_issue(
        self,
        pd: _SectionDocument,
        rd: _SectionDocument,
        expected: _SectionValue,
        observed: _SectionValue,
        conflict_kind: ConflictKind,
    ) -> ValidationIssue:
        return ValidationIssue(
            rule_id=f"SECTION-PAIR-{slugify(pd.section_code)}-{slugify(expected.canonical_key)}",
            severity=self._severity,
            message=(
                f"PD/RD section value mismatch for {expected.key!r}: "
                f"PD={self._display_value(expected)!r}, "
                f"RD={self._display_value(observed)!r}"
            ),
            category=FindingCategory.CROSS_DOCUMENT,
            target_ref=observed.target_ref or expected.target_ref or expected.key,
            operator=ComparisonOperator.EQUALS,
            expected_value=expected.value,
            observed_value=observed.value,
            unit=expected.unit,
            problem_zone=observed.problem_zone or expected.problem_zone,
            conflict_kind=conflict_kind,
            source_id=self._source_id(pd, rd),
            evidence_modality="section-pairing",
            confidence=1.0,
        )

    def _classify_value_conflict(
        self,
        expected: _SectionValue,
        observed: _SectionValue,
    ) -> ConflictKind | None:
        expected_number = self._to_float(expected.value)
        observed_number = self._to_float(observed.value)
        if expected_number is None or observed_number is None:
            if expected.value.strip().casefold() == observed.value.strip().casefold():
                return None
            return ConflictKind.HARD_CONFLICT

        if bool(expected.unit) != bool(observed.unit):
            return ConflictKind.UNIT_MISMATCH
        if expected.unit and observed.unit:
            expected_quantity = parse_quantity(expected_number, expected.unit)
            observed_quantity = parse_quantity(observed_number, observed.unit)
            if not self._quantities_compatible(expected_quantity, observed_quantity):
                return ConflictKind.UNIT_MISMATCH
            expected_si = expected_quantity.si_value
            observed_si = observed_quantity.si_value
            if expected_si is None or observed_si is None:
                return ConflictKind.UNIT_MISMATCH
            epsilon = (
                expected.tolerance_si
                if expected.tolerance_si is not None
                else self._tolerance.epsilon_for_unit(expected.unit)
            )
            if abs(expected_si - observed_si) <= epsilon:
                return None
            return ConflictKind.HARD_CONFLICT

        epsilon = (
            expected.tolerance_si
            if expected.tolerance_si is not None
            else self._tolerance.default_epsilon
        )
        if abs(expected_number - observed_number) <= epsilon:
            return None
        return ConflictKind.HARD_CONFLICT

    def _quantities_compatible(self, left: QuantityValue, right: QuantityValue) -> bool:
        return (
            left.si_value is not None
            and right.si_value is not None
            and left.dimension == right.dimension
        )

    def _load(self, path: Path) -> _SectionDocument:
        if path.is_symlink():
            raise ValueError(f"Symlinked section inputs are not accepted: {path}")
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_file():
            raise ValueError(f"Section input is not a regular file: {path}")
        if path.suffix.lower() != ".json":
            raise ValueError("PD/RD section inputs must use the .json extension")
        size = path.stat().st_size
        if size > _MAX_SECTION_BYTES:
            raise ValueError(
                f"Section input exceeds {_MAX_SECTION_BYTES} byte limit: {path} ({size} bytes)"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid UTF-8 JSON section input: {path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("Section input root must be a JSON object")
        if payload.get("schema_version") != "1.0.0":
            raise ValueError("Section input schema_version must be '1.0.0'")

        basis = payload.get("basis")
        if basis is not None and not isinstance(basis, dict):
            raise ValueError("Section input basis must be an object when provided")
        basis_payload = basis if isinstance(basis, dict) else {}
        discipline = self._required_string(payload, "discipline").upper()
        discipline_info = canonicalize_discipline(discipline)
        values = self._parse_values(payload.get("values"), discipline_info.code)
        return _SectionDocument(
            document_id=self._required_string(payload, "document_id"),
            project_id=self._required_string(payload, "project_id"),
            stage=self._required_string(payload, "stage").upper(),
            discipline=discipline,
            discipline_info=discipline_info,
            section_code=self._required_string(payload, "section_code").upper(),
            revision=self._required_string(payload, "revision"),
            basis_document_id=self._optional_string(basis_payload.get("document_id")),
            basis_revision=self._optional_string(basis_payload.get("revision")),
            values=values,
        )

    def _parse_values(self, raw: object, discipline_code: str) -> tuple[_SectionValue, ...]:
        if not isinstance(raw, list) or not raw:
            raise ValueError("Section values must be a non-empty array")
        if len(raw) > _MAX_VALUES:
            raise ValueError(f"Section has {len(raw)} values; maximum is {_MAX_VALUES}")
        values: list[_SectionValue] = []
        seen: set[str] = set()
        seen_canonical: dict[str, str] = {}
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"values[{index}] must be a JSON object")
            key = self._required_string(item, "key")
            if not _KEY_RE.fullmatch(key):
                raise ValueError(f"values[{index}].key contains unsupported characters")
            if key in seen:
                raise ValueError(f"Duplicate section value key: {key}")
            seen.add(key)
            canonical = canonicalize_key(key, discipline_code)
            if canonical.canonical in seen_canonical:
                raise ValueError(
                    f"Ambiguous section value keys map to the same canonical key "
                    f"{canonical.canonical!r}: {seen_canonical[canonical.canonical]!r} and {key!r}"
                )
            seen_canonical[canonical.canonical] = key
            raw_value = item.get("value")
            if not isinstance(raw_value, str | int | float | bool):
                raise ValueError(f"values[{index}].value must be a scalar")
            raw_required = item.get("required_in_rd", True)
            if not isinstance(raw_required, bool):
                raise ValueError(f"values[{index}].required_in_rd must be boolean")
            raw_tolerance = item.get("tolerance_si")
            if raw_tolerance is not None and (
                not isinstance(raw_tolerance, int | float) or raw_tolerance < 0
            ):
                raise ValueError(f"values[{index}].tolerance_si must be non-negative")
            values.append(
                _SectionValue(
                    key=key,
                    canonical_key=canonical.canonical,
                    key_recognized=canonical.recognized,
                    value=self._scalar_string(raw_value),
                    unit=self._optional_string(item.get("unit")),
                    target_ref=self._optional_string(item.get("target_ref")),
                    source_ref=self._optional_string(item.get("source_ref")),
                    problem_zone=self._parse_problem_zone(item.get("problem_zone"), index),
                    required_in_rd=raw_required,
                    tolerance_si=float(raw_tolerance) if raw_tolerance is not None else None,
                )
            )
        return tuple(values)

    def _parse_problem_zone(self, raw: object, index: int) -> ProblemZone | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            raise ValueError(f"values[{index}].problem_zone must be an object")
        allowed = {"sheet_id", "page_number", "x", "y", "width", "height", "element_guid"}
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError(
                f"values[{index}].problem_zone has unsupported fields: {sorted(unknown)}"
            )
        return ProblemZone(**raw)

    def _required_string(self, payload: dict[str, Any], key: str) -> str:
        value = self._optional_string(payload.get(key))
        if value is None:
            raise ValueError(f"Section input {key} must be a non-empty string")
        return value

    def _optional_string(self, raw: object) -> str | None:
        if raw is None:
            return None
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("Optional section string fields must be non-empty when provided")
        normalized = raw.strip()
        if len(normalized) > 512:
            raise ValueError("Section string field exceeds 512 characters")
        return normalized

    def _scalar_string(self, raw: object) -> str:
        if isinstance(raw, bool):
            return "true" if raw else "false"
        return str(raw).strip()

    def _to_float(self, raw: str) -> float | None:
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None

    def _display_value(self, value: _SectionValue) -> str:
        return f"{value.value} {value.unit}".strip() if value.unit else value.value

    def _source_id(self, pd: _SectionDocument, rd: _SectionDocument) -> str:
        return f"{pd.document_id}@{pd.revision}|{rd.document_id}@{rd.revision}"
