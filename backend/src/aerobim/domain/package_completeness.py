"""Deterministic package completeness assessment (WP-05).

Domain-pure checks over a declared package inventory:

* mandatory PD sections present (fail-closed ERROR naming the missing section)
* format honesty (open/exchange formats accepted; native DWG never claimed supported)
* sheet cipher / naming consistency
* statements (ведомости) and specifications presence
* PD/RD pairing by discipline section

Claim boundary: fixture-grade structural completeness only. Not statutory PP-87
exhaustiveness, not customer intake closure, not native DWG analysis.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from aerobim.domain.documentation_standard_edition import select_documentation_standard_edition
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.section_pairing import canonicalize_discipline
from aerobim.domain.stale_norm_citations import warn_if_using_superseded_edition

INVENTORY_SCHEMA_V1 = "aerobim_package_inventory_v1"

CLAIM_BOUNDARY = (
    "Engineering package-completeness only (declared inventory / fixture). "
    "Not statutory PP-87 exhaustiveness, not customer intake closure, "
    "not native DWG/RVT/NWD analysis."
)

ArtifactRole = Literal[
    "pd_section",
    "rd_section",
    "drawing",
    "specification",
    "schedule",
    "ifc",
    "ids",
    "calculation",
    "technical_spec",
    "other",
]

# Fixture-grade residential PD baseline (not a full regulatory claim).
DEFAULT_RESIDENTIAL_MANDATORY_PD: tuple[str, ...] = ("PZ", "AR", "KZH")

# Accepted exchange / open formats for honesty checks.
_ACCEPTED_EXCHANGE_FORMATS = frozenset(
    {
        "ifc",
        "ifczip",
        "ids",
        "pdf",
        "dxf",
        "json",
        "xml",
        "txt",
        "csv",
        "xlsx",
        "xls",
        "docx",
        "png",
        "jpg",
        "jpeg",
        "webp",
        "tif",
        "tiff",
    }
)

# Declared but explicitly unsupported for analysis (honesty gate).
_UNSUPPORTED_NATIVE_FORMATS = frozenset({"dwg", "rvt", "rte", "nwd", "nwc"})


@dataclass(frozen=True)
class PackageArtifact:
    """One declared artifact in a package inventory."""

    artifact_id: str
    role: ArtifactRole
    discipline: str | None = None
    section_code: str | None = None
    stage: str | None = None
    format: str | None = None
    cipher: str | None = None
    sheet_id: str | None = None
    path_hint: str | None = None
    has_specification: bool = False
    has_schedule: bool = False
    content_topics: tuple[str, ...] = ()
    has_justification: bool = False

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> PackageArtifact:
        role_raw = str(payload.get("role") or "other").strip().casefold().replace("-", "_")
        role: ArtifactRole
        if role_raw in {
            "pd_section",
            "rd_section",
            "drawing",
            "specification",
            "schedule",
            "ifc",
            "ids",
            "calculation",
            "technical_spec",
            "other",
        }:
            role = role_raw  # type: ignore[assignment]
        else:
            role = "other"
        topics_raw = payload.get("content_topics") or payload.get("topics") or ()
        topics: list[str] = []
        if isinstance(topics_raw, Sequence) and not isinstance(topics_raw, (str, bytes)):
            topics = [str(item).strip() for item in topics_raw if str(item).strip()]
        return cls(
            artifact_id=str(payload.get("artifact_id") or payload.get("id") or "").strip()
            or "unnamed",
            role=role,
            discipline=_optional_str(payload.get("discipline")),
            section_code=_optional_str(payload.get("section_code")),
            stage=_optional_str(payload.get("stage")),
            format=_optional_str(payload.get("format")),
            cipher=_optional_str(payload.get("cipher")),
            sheet_id=_optional_str(payload.get("sheet_id")),
            path_hint=_optional_str(payload.get("path_hint") or payload.get("path")),
            has_specification=bool(payload.get("has_specification", False)),
            has_schedule=bool(payload.get("has_schedule", False)),
            content_topics=tuple(topics),
            has_justification=bool(payload.get("has_justification", False)),
        )


@dataclass(frozen=True)
class PackageInventory:
    """Declared package topology for deterministic completeness checks."""

    schema: str
    project_id: str
    artifacts: tuple[PackageArtifact, ...]
    mandatory_pd_sections: tuple[str, ...] = DEFAULT_RESIDENTIAL_MANDATORY_PD
    require_pd_rd_pairing: bool = True
    require_specifications: bool = True
    require_schedules: bool = True
    require_sheet_ciphers: bool = True
    check_technical_spec_floor_partition_topics: bool = True
    check_unjustified_pd_calculations: bool = True
    # Label only — which GOST R 21.101 edition this inventory run claims to follow.
    documentation_standard_edition: str | None = None
    package_developed_on: str | None = None
    documentation_standard_selection_source: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> PackageInventory:
        raw_artifacts = payload.get("artifacts") or ()
        artifacts: list[PackageArtifact] = []
        if isinstance(raw_artifacts, Sequence) and not isinstance(raw_artifacts, (str, bytes)):
            for entry in raw_artifacts:
                if isinstance(entry, Mapping):
                    artifacts.append(PackageArtifact.from_mapping(entry))

        mandatory_raw = payload.get("mandatory_pd_sections")
        if isinstance(mandatory_raw, Sequence) and not isinstance(mandatory_raw, (str, bytes)):
            mandatory = tuple(
                canonicalize_discipline(str(item)).code
                for item in mandatory_raw
                if str(item).strip()
            )
        else:
            mandatory = DEFAULT_RESIDENTIAL_MANDATORY_PD

        explicit_edition = _optional_str(payload.get("documentation_standard_edition"))
        developed_on = _optional_str(payload.get("package_developed_on"))
        rule_raw = payload.get("documentation_standard_selection_rule")
        rule = rule_raw if isinstance(rule_raw, Mapping) else None
        edition, source = select_documentation_standard_edition(
            package_developed_on=developed_on,
            explicit_edition=explicit_edition,
            rule=rule,
        )

        return cls(
            schema=str(payload.get("schema") or "").strip() or INVENTORY_SCHEMA_V1,
            project_id=str(payload.get("project_id") or "").strip() or "unknown",
            artifacts=tuple(artifacts),
            mandatory_pd_sections=mandatory,
            require_pd_rd_pairing=bool(payload.get("require_pd_rd_pairing", True)),
            require_specifications=bool(payload.get("require_specifications", True)),
            require_schedules=bool(payload.get("require_schedules", True)),
            require_sheet_ciphers=bool(payload.get("require_sheet_ciphers", True)),
            check_technical_spec_floor_partition_topics=bool(
                payload.get("check_technical_spec_floor_partition_topics", True)
            ),
            check_unjustified_pd_calculations=bool(
                payload.get("check_unjustified_pd_calculations", True)
            ),
            documentation_standard_edition=edition,
            package_developed_on=developed_on,
            documentation_standard_selection_source=source if edition else None,
        )


@dataclass(frozen=True)
class PackageCompletenessReport:
    """Outcome of one package-completeness assessment."""

    issues: tuple[ValidationIssue, ...]
    missing_pd_sections: tuple[str, ...] = ()
    unpaired_pd_sections: tuple[str, ...] = ()
    unsupported_formats: tuple[str, ...] = ()
    documentation_standard_edition: str | None = None
    claim_boundary: str = CLAIM_BOUNDARY

    def to_capability_status(self) -> CapabilityStatus:
        if any(issue.severity is Severity.ERROR for issue in self.issues):
            missing = ", ".join(self.missing_pd_sections) or "none"
            return CapabilityStatus(
                CapabilityState.FAILED,
                (
                    f"package completeness failed "
                    f"(missing_pd={missing}; findings={len(self.issues)}); "
                    f"{self.claim_boundary}"
                ),
            )
        return CapabilityStatus(
            CapabilityState.OK,
            f"package completeness checked (findings={len(self.issues)}); {self.claim_boundary}",
        )


def assess_package_completeness(inventory: PackageInventory) -> PackageCompletenessReport:
    """Run fail-closed deterministic completeness checks on ``inventory``."""

    issues: list[ValidationIssue] = []
    missing_pd: list[str] = []
    unpaired_pd: list[str] = []
    unsupported: list[str] = []
    claim = CLAIM_BOUNDARY
    if inventory.documentation_standard_edition:
        claim = (
            f"{CLAIM_BOUNDARY} documentation_standard_edition="
            f"{inventory.documentation_standard_edition}"
            f" (source={inventory.documentation_standard_selection_source or 'n/a'})."
        )

    if inventory.schema != INVENTORY_SCHEMA_V1:
        issues.append(
            _issue(
                rule_id="AEROBIM-PACKAGE-INVENTORY-SCHEMA",
                severity=Severity.ERROR,
                message=(
                    f"Unsupported package inventory schema {inventory.schema!r}; "
                    f"expected {INVENTORY_SCHEMA_V1}; {CLAIM_BOUNDARY}"
                ),
            )
        )

    pd_disciplines = _section_disciplines(inventory.artifacts, role="pd_section")
    rd_disciplines = _section_disciplines(inventory.artifacts, role="rd_section")

    for code in inventory.mandatory_pd_sections:
        canonical = canonicalize_discipline(code)
        if canonical.code not in pd_disciplines:
            missing_pd.append(canonical.code)
            label = canonical.label if canonical.recognized else canonical.code
            issues.append(
                _issue(
                    rule_id="AEROBIM-PACKAGE-MISSING-SECTION",
                    severity=Severity.ERROR,
                    message=(
                        f"Mandatory PD section {canonical.code} ({label}) is missing "
                        f"from package inventory; {CLAIM_BOUNDARY}"
                    ),
                    target_ref=canonical.code,
                )
            )

    if (
        "KZH" in {canonicalize_discipline(code).code for code in inventory.mandatory_pd_sections}
        and "KZH" not in pd_disciplines
        and "KR" in pd_disciplines
    ):
        issues.append(
            _issue(
                rule_id="AEROBIM-PACKAGE-KR-NOT-KZH",
                severity=Severity.WARNING,
                message=(
                    "PD inventory has KR (structures, general) but mandatory KZH "
                    "(reinforced concrete) is still missing; KR does not fill the "
                    f"KZH slot and is not statutory PP-87 certification; {CLAIM_BOUNDARY}"
                ),
                target_ref="KZH",
            )
        )

    if inventory.require_pd_rd_pairing:
        # Pair every present PD section (and every mandatory that is present).
        for code in sorted(pd_disciplines):
            if code not in rd_disciplines:
                unpaired_pd.append(code)
                info = canonicalize_discipline(code)
                label = info.label if info.recognized else code
                issues.append(
                    _issue(
                        rule_id="AEROBIM-PACKAGE-UNPAIRED-SECTION",
                        severity=Severity.ERROR,
                        message=(
                            f"PD section {code} ({label}) has no paired RD section "
                            f"in package inventory; {CLAIM_BOUNDARY}"
                        ),
                        target_ref=code,
                    )
                )

    for artifact in inventory.artifacts:
        fmt = (artifact.format or "").strip().casefold().lstrip(".")
        if not fmt:
            continue
        if fmt in _UNSUPPORTED_NATIVE_FORMATS:
            unsupported.append(fmt)
            issues.append(
                _issue(
                    rule_id="AEROBIM-PACKAGE-UNSUPPORTED-FORMAT",
                    severity=Severity.ERROR,
                    message=(
                        f"Artifact {artifact.artifact_id!r} declares format {fmt!r}; "
                        "native DWG/RVT/NWD analysis is not implemented — use IFC/PDF/DXF "
                        f"exchange formats; {CLAIM_BOUNDARY}"
                    ),
                    source_id=artifact.artifact_id,
                    target_ref=artifact.section_code or artifact.discipline,
                )
            )
        elif fmt not in _ACCEPTED_EXCHANGE_FORMATS:
            issues.append(
                _issue(
                    rule_id="AEROBIM-PACKAGE-FORMAT-UNKNOWN",
                    severity=Severity.WARNING,
                    message=(
                        f"Artifact {artifact.artifact_id!r} declares unrecognized format "
                        f"{fmt!r}; preferred exchange formats are IFC/IDS/PDF/DXF/JSON; "
                        f"{CLAIM_BOUNDARY}"
                    ),
                    source_id=artifact.artifact_id,
                )
            )

    if inventory.require_sheet_ciphers:
        for artifact in inventory.artifacts:
            if artifact.role not in {"drawing", "pd_section", "rd_section"}:
                continue
            cipher = (artifact.cipher or "").strip()
            if not cipher:
                issues.append(
                    _issue(
                        rule_id="AEROBIM-PACKAGE-MISSING-CIPHER",
                        severity=Severity.ERROR,
                        message=(
                            f"Artifact {artifact.artifact_id!r} lacks sheet cipher (шифр); "
                            f"{CLAIM_BOUNDARY}"
                        ),
                        source_id=artifact.artifact_id,
                        target_ref=artifact.sheet_id or artifact.section_code,
                    )
                )
                continue
            disc = _artifact_discipline_raw(artifact)
            if disc:
                code = canonicalize_discipline(disc).code
                folded = cipher.casefold()
                # Accept either Latin canonical or common RU aliases in cipher.
                aliases = {code.casefold(), disc.casefold()}
                if code == "AR":
                    aliases.add("ар")
                if code == "KZH":
                    aliases.update({"кж", "кж0"})
                if code == "KR":
                    aliases.update({"кр"})
                if code == "PZ":
                    aliases.add("пз")
                if not any(alias in folded for alias in aliases if alias):
                    issues.append(
                        _issue(
                            rule_id="AEROBIM-PACKAGE-CIPHER-MISMATCH",
                            severity=Severity.ERROR,
                            message=(
                                f"Artifact {artifact.artifact_id!r} cipher {cipher!r} "
                                f"does not reference discipline {code}; {CLAIM_BOUNDARY}"
                            ),
                            source_id=artifact.artifact_id,
                            target_ref=code,
                        )
                    )

    has_spec = any(a.role == "specification" or a.has_specification for a in inventory.artifacts)
    has_schedule = any(a.role == "schedule" or a.has_schedule for a in inventory.artifacts)
    if inventory.require_specifications and not has_spec:
        issues.append(
            _issue(
                rule_id="AEROBIM-PACKAGE-MISSING-SPECIFICATION",
                severity=Severity.ERROR,
                message=(
                    "Package inventory has no specification (спецификация) artifact; "
                    f"{CLAIM_BOUNDARY}"
                ),
                target_ref="specification",
            )
        )
    if inventory.require_schedules and not has_schedule:
        issues.append(
            _issue(
                rule_id="AEROBIM-PACKAGE-MISSING-SCHEDULE",
                severity=Severity.ERROR,
                message=(
                    "Package inventory has no schedule/statement (ведомость) artifact; "
                    f"{CLAIM_BOUNDARY}"
                ),
                target_ref="schedule",
            )
        )

    if inventory.check_technical_spec_floor_partition_topics:
        issues.extend(_technical_spec_floor_partition_issues(inventory.artifacts))

    if inventory.check_unjustified_pd_calculations:
        issues.extend(_unjustified_pd_calculation_issues(inventory.artifacts))

    stale = warn_if_using_superseded_edition(
        edition=inventory.documentation_standard_edition,
        package_developed_on=inventory.package_developed_on,
    )
    if stale is not None:
        issues.append(stale)

    # Stable ordering for determinism.
    issues.sort(key=lambda item: (item.rule_id, item.target_ref or "", item.message))
    return PackageCompletenessReport(
        issues=tuple(issues),
        missing_pd_sections=tuple(missing_pd),
        unpaired_pd_sections=tuple(unpaired_pd),
        unsupported_formats=tuple(sorted(set(unsupported))),
        documentation_standard_edition=inventory.documentation_standard_edition,
        claim_boundary=claim,
    )


_FLOOR_TOPIC_ALIASES = frozenset(
    {
        "floors",
        "floor",
        "floor_finishes",
        "flooring",
        "полы",
        "пол",
        "конструкции_полов",
    }
)
_PARTITION_TOPIC_ALIASES = frozenset(
    {
        "partitions",
        "partition",
        "walls_partitions",
        "перегородки",
        "перегородка",
        "внутренние_перегородки",
    }
)


def _normalize_topic(raw: str) -> str:
    return raw.strip().casefold().replace("-", "_").replace(" ", "_")


def _technical_spec_floor_partition_issues(
    artifacts: Sequence[PackageArtifact],
) -> list[ValidationIssue]:
    """KR #2: declared ТЧ must cover floors + partitions topics (inventory-level)."""
    specs = [a for a in artifacts if a.role == "technical_spec"]
    if not specs:
        return []
    union = {_normalize_topic(t) for a in specs for t in a.content_topics}
    missing: list[str] = []
    if not (union & _FLOOR_TOPIC_ALIASES):
        missing.append("floors/полы")
    if not (union & _PARTITION_TOPIC_ALIASES):
        missing.append("partitions/перегородки")
    if not missing:
        return []
    ids = ", ".join(a.artifact_id for a in specs)
    return [
        _issue(
            rule_id="AEROBIM-PACKAGE-TECHNICAL-SPEC-MISSING-TOPIC",
            severity=Severity.ERROR,
            message=(
                f"Technical specification artifact(s) [{ids}] omit declared topics "
                f"{', '.join(missing)}; inventory-level content gate only "
                f"(not OCR of ТЧ); {CLAIM_BOUNDARY}"
            ),
            source_id=specs[0].artifact_id,
            target_ref="technical_spec",
        )
    ]


def _is_pd_stage(stage: str | None) -> bool:
    if not stage:
        return False
    folded = stage.strip().casefold()
    return folded in {"pd", "пд", "project_documentation", "проектная"}


def _unjustified_pd_calculation_issues(
    artifacts: Sequence[PackageArtifact],
) -> list[ValidationIssue]:
    """KR #4: calculation declared in PD without justification marker."""
    issues: list[ValidationIssue] = []
    for artifact in artifacts:
        if artifact.role != "calculation":
            continue
        if not _is_pd_stage(artifact.stage):
            continue
        if artifact.has_justification:
            continue
        issues.append(
            _issue(
                rule_id="AEROBIM-PACKAGE-UNJUSTIFIED-CALCULATION",
                severity=Severity.ERROR,
                message=(
                    f"Calculation artifact {artifact.artifact_id!r} is declared in PD "
                    "without has_justification=true; unjustified calc-in-PD inventory "
                    f"gate only (not engineering correctness); {CLAIM_BOUNDARY}"
                ),
                source_id=artifact.artifact_id,
                target_ref=artifact.discipline or artifact.section_code or "calculation",
            )
        )
    return issues


def _artifact_discipline_raw(artifact: PackageArtifact) -> str | None:
    """Resolve inventory discipline without treating PP-87 volume numbers as codes.

    Numeric ``section_code`` (e.g. ``3``) is a document-volume label, not AR/KR.
    Prefer ``discipline`` in that case. Still not statutory PP-87 completeness.
    """

    section = (artifact.section_code or "").strip()
    discipline = (artifact.discipline or "").strip()
    if section.isdigit():
        return discipline or section
    return section or discipline or None


def _section_disciplines(
    artifacts: Sequence[PackageArtifact],
    *,
    role: ArtifactRole,
) -> set[str]:
    codes: set[str] = set()
    for artifact in artifacts:
        if artifact.role != role:
            continue
        raw = _artifact_discipline_raw(artifact)
        if not raw:
            continue
        codes.add(canonicalize_discipline(raw).code)
    return codes


def _issue(
    *,
    rule_id: str,
    severity: Severity,
    message: str,
    source_id: str | None = None,
    target_ref: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        category=FindingCategory.CROSS_DOCUMENT,
        source_id=source_id or "package-completeness",
        origin="deterministic",
        target_ref=target_ref,
        evidence_refs=("claim_boundary:package_completeness_ENG_PARTIAL",),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "CLAIM_BOUNDARY",
    "DEFAULT_RESIDENTIAL_MANDATORY_PD",
    "INVENTORY_SCHEMA_V1",
    "PackageArtifact",
    "PackageCompletenessReport",
    "PackageInventory",
    "assess_package_completeness",
]
