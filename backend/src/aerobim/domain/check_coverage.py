"""Check-coverage map (P0): per-source × check-family status (competitive brief P0.1/P0.5).

Делает ключевое различие явным ПО КАЖДОМУ ИСТОЧНИКУ: «нарушений не найдено» — это НЕ
то же самое, что «не проверялось».

Честность (после Red Team): ``CHECKED_OK`` выставляется ТОЛЬКО когда (а) вызывающий
явно передал ``scope`` и источник входит в область данного семейства, И (б) ВСЕ
возможности семейства = OK, И (в) находок нет. Без scope или при частично-выполненной
проверке — ``NOT_CHECKED`` (глобальный OK возможности сам по себе НЕ значит, что данный
источник проверялся). Находки с неизвестным/``None`` источником не исчезают — они
попадают в строку ``(unattributed)``.

Domain-pure, **VERDICT-NEUTRAL**: наблюдаемость, выведенная из детерминированного
отчёта; НЕ выставляет и не меняет ``summary.passed`` (ADR-001). Термины: coverage map —
карта покрытия; family — семейство проверок; scope — область проверки.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    RuleScope,
    ValidationIssue,
    ValidationReport,
)

COVERAGE_ALGORITHM_VERSION = "1.1.0"
"""Bump when the coverage derivation changes so frozen snapshots stay interpretable."""


class CoverageStatus(StrEnum):
    """Явный статус покрытия источника по семейству проверок."""

    CHECKED_OK = "checked_ok"
    """Проверка выполнялась НА ЭТОМ ИСТОЧНИКЕ (scope) и находок нет."""
    CHECKED_FINDINGS = "checked_findings"
    """Есть детерминированные находки."""
    NOT_CHECKED = "not_checked"
    """Проверка не выполнялась / область неизвестна — «нет находок» ≠ «нет нарушений»."""
    INSUFFICIENT_DATA = "insufficient_data"
    """Проверка запускалась, но не завершилась (какая-то возможность семейства FAILED)."""
    REQUIRES_EXPERT = "requires_expert"
    """Только advisory-находки — требуется подтверждение эксперта."""


# Operator-facing labels (KT#2): do not invent a second SSOT — aliases over CoverageStatus.
_OPERATOR_STATUS: dict[CoverageStatus, str] = {
    CoverageStatus.CHECKED_OK: "done",
    CoverageStatus.CHECKED_FINDINGS: "findings",
    CoverageStatus.NOT_CHECKED: "not_done",
    CoverageStatus.INSUFFICIENT_DATA: "partial",
    CoverageStatus.REQUIRES_EXPERT: "needs_expert",
}

OPERATOR_STATUS_LEGEND: dict[str, str] = {
    "done": "Проверка выполнена на этом источнике; нарушений не найдено",
    "findings": "Проверка выполнена; есть детерминированные находки",
    "not_done": "Проверка не выполнялась / область неизвестна (≠ «нарушений нет»)",
    "partial": "Проверка запускалась, данных или движка недостаточно",
    "needs_expert": "Только advisory-сигнал — требуется эксперт",
}


def operator_status_for(status: CoverageStatus) -> str:
    """Presentation alias for TIM / UI — same honesty as CoverageStatus."""

    return _OPERATOR_STATUS[status]

# Семейство -> НАБОР полей ReportCapabilities, влияющих на это семейство. CHECKED_OK
# требует, чтобы ВСЕ они были OK (worst-state агрегация); любой FAILED -> INSUFFICIENT_DATA.
_FAMILY_CAPABILITIES: dict[FindingCategory, tuple[str, ...]] = {
    FindingCategory.IFC_VALIDATION: ("ifc_validation", "ifc_schema"),
    FindingCategory.IDS_VALIDATION: ("ids",),
    FindingCategory.DRAWING_VALIDATION: ("raster",),
    FindingCategory.CROSS_DOCUMENT: ("section_pairing",),
    FindingCategory.SPATIAL: ("clash", "mep_system_clash"),
}

_UNATTRIBUTED = "(unattributed)"


@dataclass(frozen=True)
class SourceCoverage:
    """Покрытие одного источника по всем семействам проверок."""

    source_id: str
    families: tuple[tuple[FindingCategory, CoverageStatus], ...]
    reasons: tuple[tuple[FindingCategory, str], ...] = ()

    def status_for(self, family: FindingCategory) -> CoverageStatus:
        for fam, status in self.families:
            if fam is family:
                return status
        return CoverageStatus.NOT_CHECKED


@dataclass(frozen=True)
class CheckCoverageMap:
    """Карта покрытия комплекта: строка на источник. Verdict-neutral артефакт."""

    rows: tuple[SourceCoverage, ...]

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {status.value: 0 for status in CoverageStatus}
        for row in self.rows:
            for _family, status in row.families:
                counts[status.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "check-coverage-map",
            "schema_version": COVERAGE_ALGORITHM_VERSION,
            "note": (
                "per-source check coverage; 'no findings' != 'not checked'; CHECKED_OK "
                "requires explicit scope + all family capabilities OK; verdict-neutral — "
                "does NOT set summary.passed (ADR-001). operator_status is a presentation "
                "alias (done/findings/not_done/partial/needs_expert), not a product claim."
            ),
            "operator_legend": dict(OPERATOR_STATUS_LEGEND),
            "sources": [
                {
                    "source_id": row.source_id,
                    "families": {fam.value: status.value for fam, status in row.families},
                    "operator_status": {
                        fam.value: operator_status_for(status) for fam, status in row.families
                    },
                    "reasons": {fam.value: reason for fam, reason in row.reasons},
                }
                for row in self.rows
            ],
            "summary": self.summary(),
            "operator_summary": {
                operator_status_for(status): count
                for status, count in (
                    (CoverageStatus(k), v) for k, v in self.summary().items() if v
                )
            },
        }


def _family_states(
    capabilities: ReportCapabilities, family: FindingCategory
) -> list[CapabilityState]:
    states: list[CapabilityState] = []
    for field in _FAMILY_CAPABILITIES.get(family, ()):
        value = getattr(capabilities, field, None)
        if isinstance(value, CapabilityStatus):
            states.append(value.status)
    return states


def _status_without_findings(
    capabilities: ReportCapabilities,
    family: FindingCategory,
    source_id: str,
    scope: Mapping[FindingCategory, AbstractSet[str]] | None,
) -> tuple[CoverageStatus, str | None]:
    states = _family_states(capabilities, family)
    if not states:
        return CoverageStatus.NOT_CHECKED, "no capability mapping for this check family"
    # Known-out-of-scope: this source was not part of this check at all, regardless of
    # the family's global capability state (a family failure does not concern it).
    if scope is not None and family in scope and source_id not in scope[family]:
        return CoverageStatus.NOT_CHECKED, "source not in scope of this check"
    if any(state is CapabilityState.FAILED for state in states):
        return CoverageStatus.INSUFFICIENT_DATA, "a check in this family failed"
    if not all(state is CapabilityState.OK for state in states):
        # SKIPPED / MISSING / NOT_VERIFIED / NOT_IMPLEMENTED -> not fully run.
        return CoverageStatus.NOT_CHECKED, "check family did not fully run"
    # All family capabilities OK: CHECKED_OK still requires EXPLICIT per-source scope,
    # otherwise a global OK would falsely mark an out-of-scope source as checked.
    if scope is None or family not in scope:
        return CoverageStatus.NOT_CHECKED, "check ran but per-source scope is unknown"
    return CoverageStatus.CHECKED_OK, None


def _has_finding(
    issues: Sequence[ValidationIssue], source_id: str, family: FindingCategory, *, advisory: bool
) -> bool:
    for issue in issues:
        if issue.source_id != source_id or issue.category is not family:
            continue
        # Exclusion-based: unknown/None origin counts as deterministic (never dropped).
        is_advisory = issue.origin == "advisory"
        if is_advisory == advisory:
            return True
    return False


def _unattributed_row(
    issues: Sequence[ValidationIssue], known: AbstractSet[str]
) -> SourceCoverage | None:
    det_families: set[FindingCategory] = set()
    adv_families: set[FindingCategory] = set()
    for issue in issues:
        if issue.source_id in known:
            continue  # attributed to a listed source (None/"" are never in `known`)
        if issue.origin == "advisory":
            adv_families.add(issue.category)
        else:
            det_families.add(issue.category)
    if not det_families and not adv_families:
        return None
    fam_status: list[tuple[FindingCategory, CoverageStatus]] = []
    fam_reason: list[tuple[FindingCategory, str]] = []
    for family in FindingCategory:
        if family in det_families:
            fam_status.append((family, CoverageStatus.CHECKED_FINDINGS))
            fam_reason.append((family, "finding not attributed to a listed source id"))
        elif family in adv_families:
            fam_status.append((family, CoverageStatus.REQUIRES_EXPERT))
            fam_reason.append((family, "advisory finding not attributed to a listed source id"))
        else:
            fam_status.append((family, CoverageStatus.NOT_CHECKED))
    return SourceCoverage(
        source_id=_UNATTRIBUTED, families=tuple(fam_status), reasons=tuple(fam_reason)
    )


def build_check_coverage(
    *,
    source_ids: Sequence[str],
    issues: Sequence[ValidationIssue],
    capabilities: ReportCapabilities | None = None,
    scope: Mapping[FindingCategory, AbstractSet[str]] | None = None,
) -> CheckCoverageMap:
    """Derive a per-source × check-family coverage map (verdict-neutral).

    Per (source, family): a deterministic finding -> CHECKED_FINDINGS; advisory-only ->
    REQUIRES_EXPERT; no finding + all family capabilities OK + source in ``scope[family]``
    -> CHECKED_OK; a FAILED family capability -> INSUFFICIENT_DATA; otherwise NOT_CHECKED.
    Findings whose ``source_id`` is unknown/None are surfaced in an ``(unattributed)`` row
    so a real finding can never silently vanish while other rows read CHECKED_OK.
    """
    caps = capabilities if capabilities is not None else ReportCapabilities()
    unique_sources = list(dict.fromkeys(sid for sid in source_ids if sid))
    known = set(unique_sources)

    rows: list[SourceCoverage] = []
    for sid in unique_sources:
        fam_status: list[tuple[FindingCategory, CoverageStatus]] = []
        fam_reason: list[tuple[FindingCategory, str]] = []
        for family in FindingCategory:
            if _has_finding(issues, sid, family, advisory=False):
                status: CoverageStatus = CoverageStatus.CHECKED_FINDINGS
                reason: str | None = None
            elif _has_finding(issues, sid, family, advisory=True):
                status = CoverageStatus.REQUIRES_EXPERT
                reason = "advisory-only findings require expert confirmation"
            else:
                status, reason = _status_without_findings(caps, family, sid, scope)
            fam_status.append((family, status))
            if reason:
                fam_reason.append((family, reason))
        rows.append(
            SourceCoverage(source_id=sid, families=tuple(fam_status), reasons=tuple(fam_reason))
        )

    unattributed = _unattributed_row(issues, known)
    if unattributed is not None:
        rows.append(unattributed)
    return CheckCoverageMap(rows=tuple(rows))


def coverage_from_report(
    report: ValidationReport,
    *,
    scope: Mapping[FindingCategory, AbstractSet[str]] | None = None,
) -> CheckCoverageMap:
    """Build a coverage map from a report's DECLARED inputs + findings (verdict-neutral).

    ``source_ids`` = declared requirement sources + drawing sheet ids. Engine-internal
    finding source ids (e.g. ``clash``) that are not declared inputs surface in the
    ``(unattributed)`` row (never silently dropped). ``scope`` is optional: until the
    analyze use case captures per-source scope, pass ``None`` — a source with no finding
    then reads NOT_CHECKED (honest: not known to be in scope), never a fabricated
    CHECKED_OK. Does NOT read or set ``summary.passed`` (ADR-001).
    """
    declared: list[str] = []
    for requirement in report.requirements:
        if requirement.source:
            declared.append(requirement.source)
    for annotation in report.drawing_annotations:
        if annotation.sheet_id:
            declared.append(annotation.sheet_id)
    for region in report.drawing_regions:
        if region.sheet_id:
            declared.append(region.sheet_id)
    for asset in report.drawing_assets:
        if asset.sheet_id:
            declared.append(asset.sheet_id)
    return build_check_coverage(
        source_ids=declared,
        issues=report.issues,
        capabilities=report.capabilities,
        scope=scope,
    )


def _capability_ok(capability: object) -> bool:
    return isinstance(capability, CapabilityStatus) and capability.status is CapabilityState.OK


def derive_report_scope(report: ValidationReport) -> dict[FindingCategory, set[str]]:
    """Per-source scope derived from a report by EVIDENCE OF PROCESSING (not co-occurrence).

    Honest derivation (after Red Team): a source is scoped for a family only when the
    report shows that family actually processed it.
    - IFC_VALIDATION: only sources contributing an IFC-scoped rule (the IFC validator skips
      drawing-annotation rules), and only when ``ifc_validation`` is OK.
    - DRAWING_VALIDATION: only sheets with extracted annotations/regions (evidence of OCR
      yield — NOT asset-only/zero-yield sheets), and only when ``raster`` is OK.
    - IDS and CROSS_DOCUMENT are intentionally NOT auto-scoped: an OK ``ids`` proves the IDS
      XML was validated against the model (not that a requirement source was processed), and
      ``section_pairing`` proves only the PD/RD pair. Those stay NOT_CHECKED honestly until
      the analyze use case records true per-source scope. SPATIAL is element/model-level.
    """
    caps = report.capabilities if report.capabilities is not None else ReportCapabilities()
    ifc_sources = {
        req.source
        for req in report.requirements
        if req.source and req.rule_scope in (RuleScope.IFC_PROPERTY, RuleScope.IFC_QUANTITY)
    }
    # Only sheets with processing evidence (annotations/regions); assets register file
    # presence, not OCR yield, so a zero-yield sheet must not look auto-read.
    sheet_sources: set[str] = set()
    for annotation in report.drawing_annotations:
        if annotation.sheet_id:
            sheet_sources.add(annotation.sheet_id)
    for region in report.drawing_regions:
        if region.sheet_id:
            sheet_sources.add(region.sheet_id)

    scope: dict[FindingCategory, set[str]] = {}
    if _capability_ok(caps.ifc_validation):
        scope[FindingCategory.IFC_VALIDATION] = ifc_sources
    if _capability_ok(caps.raster):
        # DRAWING_VALIDATION findings are attributed to the requirement source (e.g. spec.pdf),
        # NOT the sheet id. If any such finding is attributed off-sheet, granting per-sheet
        # DRAWING scope would let a sheet read CHECKED_OK while a drawing finding exists ->
        # omit DRAWING scope entirely (sheets stay NOT_CHECKED honestly).
        offsheet_drawing_finding = any(
            issue.category is FindingCategory.DRAWING_VALIDATION
            and issue.source_id not in sheet_sources
            for issue in report.issues
        )
        if not offsheet_drawing_finding:
            scope[FindingCategory.DRAWING_VALIDATION] = sheet_sources
    return scope


__all__ = [
    "COVERAGE_ALGORITHM_VERSION",
    "CheckCoverageMap",
    "CoverageStatus",
    "SourceCoverage",
    "build_check_coverage",
    "coverage_from_report",
    "derive_report_scope",
]
