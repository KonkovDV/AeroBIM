"""Check-coverage map (P0): per-source × check-family status (competitive brief P0.1/P0.5).

Делает ключевое различие явным ПО КАЖДОМУ ИСТОЧНИКУ: «нарушений не найдено» — это НЕ
то же самое, что «не проверялось». Источник получает ``CHECKED_OK`` по семейству
проверок ТОЛЬКО если эта проверка реально выполнялась (capability OK) и находок нет;
если проверка не выполнялась — источник ``NOT_CHECKED`` (никогда не «тихий OK»).

Domain-pure, **VERDICT-NEUTRAL**: это наблюдаемость/отчётность, выведенная из
детерминированного отчёта; НЕ выставляет и не меняет ``summary.passed`` (ADR-001).
Английские термины: coverage map — карта покрытия; family — семейство проверок.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ReportCapabilities,
    ValidationIssue,
)


class CoverageStatus(StrEnum):
    """Явный статус покрытия источника по семейству проверок."""

    CHECKED_OK = "checked_ok"
    """Проверка выполнялась и находок нет (НЕ выставляется, если проверка не шла)."""
    CHECKED_FINDINGS = "checked_findings"
    """Проверка выполнялась и есть детерминированные находки."""
    NOT_CHECKED = "not_checked"
    """Проверка не выполнялась — «нет находок» здесь не значит «нет нарушений»."""
    INSUFFICIENT_DATA = "insufficient_data"
    """Проверка запускалась, но не завершилась (capability FAILED)."""
    REQUIRES_EXPERT = "requires_expert"
    """Только advisory-находки — требуется подтверждение эксперта."""


# Семейство проверок -> поле ReportCapabilities, говорящее, ВЫПОЛНЯЛАСЬ ли проверка.
_FAMILY_CAPABILITY: dict[FindingCategory, str] = {
    FindingCategory.IFC_VALIDATION: "ifc_validation",
    FindingCategory.IDS_VALIDATION: "ids",
    FindingCategory.DRAWING_VALIDATION: "raster",
    FindingCategory.CROSS_DOCUMENT: "section_pairing",
    FindingCategory.SPATIAL: "clash",
}


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
                "per-source check coverage; 'no findings' != 'not checked'; "
                "verdict-neutral — does NOT set summary.passed (ADR-001)"
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


def _capability_for(
    capabilities: ReportCapabilities, family: FindingCategory
) -> CapabilityStatus | None:
    field = _FAMILY_CAPABILITY.get(family)
    if field is None:
        return None
    value = getattr(capabilities, field, None)
    return value if isinstance(value, CapabilityStatus) else None


def _status_without_findings(
    capability: CapabilityStatus | None,
) -> tuple[CoverageStatus, str | None]:
    if capability is None:
        return CoverageStatus.NOT_CHECKED, "no capability mapping for this check family"
    if capability.status is CapabilityState.OK:
        return CoverageStatus.CHECKED_OK, None
    if capability.status is CapabilityState.FAILED:
        return CoverageStatus.INSUFFICIENT_DATA, capability.reason
    # SKIPPED / MISSING / NOT_VERIFIED / NOT_IMPLEMENTED -> the check did not run.
    return CoverageStatus.NOT_CHECKED, capability.reason


def build_check_coverage(
    *,
    source_ids: Sequence[str],
    issues: Sequence[ValidationIssue],
    capabilities: ReportCapabilities | None = None,
) -> CheckCoverageMap:
    """Derive a per-source × check-family coverage map (verdict-neutral).

    Rules per (source_id, family): a deterministic finding -> CHECKED_FINDINGS;
    advisory-only finding -> REQUIRES_EXPERT; no finding + capability OK -> CHECKED_OK;
    + capability FAILED -> INSUFFICIENT_DATA; otherwise (not run) -> NOT_CHECKED.
    """
    caps = capabilities if capabilities is not None else ReportCapabilities()
    unique_sources = list(dict.fromkeys(sid for sid in source_ids if sid))

    rows: list[SourceCoverage] = []
    for sid in unique_sources:
        fam_status: list[tuple[FindingCategory, CoverageStatus]] = []
        fam_reason: list[tuple[FindingCategory, str]] = []
        for family in FindingCategory:
            deterministic = any(
                issue.source_id == sid
                and issue.category is family
                and (issue.origin or "deterministic") == "deterministic"
                for issue in issues
            )
            advisory = any(
                issue.source_id == sid and issue.category is family and issue.origin == "advisory"
                for issue in issues
            )
            if deterministic:
                status: CoverageStatus = CoverageStatus.CHECKED_FINDINGS
                reason: str | None = None
            elif advisory:
                status = CoverageStatus.REQUIRES_EXPERT
                reason = "advisory-only findings require expert confirmation"
            else:
                status, reason = _status_without_findings(_capability_for(caps, family))
            fam_status.append((family, status))
            if reason:
                fam_reason.append((family, reason))
        rows.append(
            SourceCoverage(source_id=sid, families=tuple(fam_status), reasons=tuple(fam_reason))
        )
    return CheckCoverageMap(rows=tuple(rows))


__all__ = [
    "CheckCoverageMap",
    "CoverageStatus",
    "SourceCoverage",
    "build_check_coverage",
]
