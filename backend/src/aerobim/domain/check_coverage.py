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
    ValidationIssue,
    ValidationReport,
)


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
            "note": (
                "per-source check coverage; 'no findings' != 'not checked'; CHECKED_OK "
                "requires explicit scope + all family capabilities OK; verdict-neutral — "
                "does NOT set summary.passed (ADR-001)"
            ),
            "sources": [
                {
                    "source_id": row.source_id,
                    "families": {fam.value: status.value for fam, status in row.families},
                    "reasons": {fam.value: reason for fam, reason in row.reasons},
                }
                for row in self.rows
            ],
            "summary": self.summary(),
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
    """Provable per-source scope derived from a report's DECLARED inputs + capabilities.

    A declared requirement source is in scope for a family whose check provably ran (its
    capability is OK) and which processes requirement content: IFC_VALIDATION / IDS /
    CROSS_DOCUMENT. Drawing sheets are in scope for DRAWING_VALIDATION when raster ran.
    SPATIAL (clash) is element/model-level, NOT per-document, so it is intentionally not
    per-source scoped here (doc/sheet sources stay NOT_CHECKED for SPATIAL). Conservative:
    scope is granted only when the capability is OK, so CHECKED_OK stays honest.
    """
    caps = report.capabilities if report.capabilities is not None else ReportCapabilities()
    doc_sources = {req.source for req in report.requirements if req.source}
    sheet_sources: set[str] = set()
    for annotation in report.drawing_annotations:
        if annotation.sheet_id:
            sheet_sources.add(annotation.sheet_id)
    for region in report.drawing_regions:
        if region.sheet_id:
            sheet_sources.add(region.sheet_id)
    for asset in report.drawing_assets:
        if asset.sheet_id:
            sheet_sources.add(asset.sheet_id)

    scope: dict[FindingCategory, set[str]] = {}
    if _capability_ok(caps.ifc_validation):
        scope[FindingCategory.IFC_VALIDATION] = doc_sources
    if _capability_ok(caps.ids):
        scope[FindingCategory.IDS_VALIDATION] = doc_sources
    if _capability_ok(caps.section_pairing):
        scope[FindingCategory.CROSS_DOCUMENT] = doc_sources
    if _capability_ok(caps.raster):
        scope[FindingCategory.DRAWING_VALIDATION] = sheet_sources
    return scope


__all__ = [
    "CheckCoverageMap",
    "CoverageStatus",
    "SourceCoverage",
    "build_check_coverage",
    "coverage_from_report",
    "derive_report_scope",
]
