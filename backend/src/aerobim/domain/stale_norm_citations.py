"""Warn when a citation names a superseded standard.

Demo case: Moscow CIM AGR requirements still cite GOST R 21.101-2020 after
GOST R 21.101-2026 took effect on 2026-04-01 (Rosstandart 129-st, 12.02.2026).
Domain-pure: catalog mappings are passed in; no file I/O, no clock.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

RULE_SUPERSEDED = "AEROBIM-NORM-SUPERSEDED"
CLAIM_BOUNDARY = (
    "Citation hygiene only. Not statutory interpretation of the replacement "
    "standard. Not Moscow AGR completeness. Not customer accuracy."
)
# Same cutoff as samples/config/documentation-standard-edition.json
GOST_21_101_2020 = "21.101-2020"
GOST_21_101_2026 = "21.101-2026"
GOST_21_101_CUTOFF_EXCLUSIVE = "2026-04-01"


@dataclass(frozen=True)
class NormDocument:
    doc_id: str
    aliases: tuple[str, ...]
    status: str
    replaced_by: str | None = None
    replaced_on: str | None = None
    authority: str | None = None
    url: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> NormDocument:
        aliases_raw = payload.get("aliases") or ()
        aliases: tuple[str, ...] = ()
        if isinstance(aliases_raw, Sequence) and not isinstance(aliases_raw, (str, bytes)):
            aliases = tuple(str(item).strip() for item in aliases_raw if str(item).strip())
        return cls(
            doc_id=str(payload.get("id") or payload.get("doc_id") or "").strip(),
            aliases=aliases,
            status=str(payload.get("status") or "").strip().casefold(),
            replaced_by=_opt(payload.get("replaced_by")),
            replaced_on=_opt(payload.get("replaced_on")),
            authority=_opt(payload.get("authority")),
            url=_opt(payload.get("url")),
        )


@dataclass(frozen=True)
class CitingSource:
    source_id: str
    title: str
    cites: tuple[str, ...]
    as_of: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> CitingSource:
        cites_raw = payload.get("cites") or ()
        cites: tuple[str, ...] = ()
        if isinstance(cites_raw, Sequence) and not isinstance(cites_raw, (str, bytes)):
            cites = tuple(str(item).strip() for item in cites_raw if str(item).strip())
        return cls(
            source_id=str(payload.get("id") or payload.get("source_id") or "").strip(),
            title=str(payload.get("title") or "").strip() or "untitled",
            cites=cites,
            as_of=str(payload.get("as_of") or "").strip(),
        )


def _opt(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _fold(text: str) -> str:
    return text.strip().casefold().replace(" ", "").replace("ё", "е")


def _document_matches(document: NormDocument, citation: str) -> bool:
    needle = _fold(citation)
    if not needle:
        return False
    names = (document.doc_id, *document.aliases)
    return any(_fold(name) in needle or needle in _fold(name) for name in names if name)


def warn_if_using_superseded_edition(
    *,
    edition: str | None,
    package_developed_on: str | None,
    cutoff_exclusive: str = GOST_21_101_CUTOFF_EXCLUSIVE,
    superseded_id: str = GOST_21_101_2020,
    replacement_id: str = GOST_21_101_2026,
) -> ValidationIssue | None:
    """Warn when a pack is labeled with a superseded GOST R 21.101 edition.

    Historical packs (developed before the cutoff) keep the 2020 label without
    a warning. Missing developed-on + 2020 label warns: operator must date the pack.
    """

    if not edition or _fold(superseded_id) not in _fold(edition):
        return None
    developed = (package_developed_on or "").strip()
    if developed and developed < cutoff_exclusive:
        return None
    if developed:
        reason = (
            f"package_developed_on={developed} is on/after {cutoff_exclusive}, "
            f"but documentation_standard_edition={edition}"
        )
    else:
        reason = (
            f"documentation_standard_edition={edition} with no package_developed_on; "
            f"{superseded_id} is superseded as of {cutoff_exclusive}"
        )
    return ValidationIssue(
        rule_id=RULE_SUPERSEDED,
        severity=Severity.WARNING,
        message=(
            f"{reason}; replacement {replacement_id} (Rosstandart 129-st, "
            f"12.02.2026, in force 01.04.2026); {CLAIM_BOUNDARY}"
        ),
        category=FindingCategory.CROSS_DOCUMENT,
        origin="deterministic",
        expected_value=replacement_id,
        observed_value=edition,
        evidence_refs=("claim_boundary:stale_norm_citation",),
        source_id="documentation-standard-edition",
    )


def collect_stale_citation_issues(
    documents: Sequence[NormDocument],
    sources: Sequence[CitingSource],
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for source in sources:
        as_of = (source.as_of or "").strip()
        for citation in source.cites:
            for document in documents:
                if document.status != "superseded":
                    continue
                if not _document_matches(document, citation):
                    continue
                replaced_on = (document.replaced_on or "").strip()
                if as_of and replaced_on and as_of < replaced_on:
                    continue
                replacement = document.replaced_by or "(unspecified replacement)"
                issues.append(
                    ValidationIssue(
                        rule_id=RULE_SUPERSEDED,
                        severity=Severity.WARNING,
                        message=(
                            f"{source.title} ({source.source_id}) cites {citation} "
                            f"as of {as_of or '(no as_of)'}; that document is superseded"
                            f"{f' on {replaced_on}' if replaced_on else ''} by "
                            f"{replacement}"
                            f"{f'; {document.authority}' if document.authority else ''}"
                            f"{f'; {document.url}' if document.url else ''}; "
                            f"{CLAIM_BOUNDARY}"
                        ),
                        category=FindingCategory.CROSS_DOCUMENT,
                        origin="deterministic",
                        expected_value=replacement,
                        observed_value=citation,
                        source_id=source.source_id,
                        evidence_refs=("claim_boundary:stale_norm_citation",),
                    )
                )
    issues.sort(key=lambda item: (item.source_id or "", item.message))
    return tuple(issues)
