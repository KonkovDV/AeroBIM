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

from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.section_pairing import canonicalize_discipline

INVENTORY_SCHEMA_V1 = "aerobim_package_inventory_v1"

CLAIM_BOUNDARY = (
    "Engineering package-completeness only (declared inventory / fixture). "
    "Not statutory PP-87 exhaustiveness, not customer intake closure, "
    "not native DWG analysis."
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
        "png",
        "jpg",
        "jpeg",
        "webp",
        "tif",
        "tiff",
    }
)

# Declared but explicitly unsupported for analysis (honesty gate).
_UNSUPPORTED_NATIVE_FORMATS = frozenset({"dwg"})


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

        return cls(
            schema=str(payload.get("schema") or "").strip() or INVENTORY_SCHEMA_V1,
            project_id=str(payload.get("project_id") or "").strip() or "unknown",
            artifacts=tuple(artifacts),
            mandatory_pd_sections=mandatory,
            require_pd_rd_pairing=bool(payload.get("require_pd_rd_pairing", True)),
            require_specifications=bool(payload.get("require_specifications", True)),
            require_schedules=bool(payload.get("require_schedules", True)),
            require_sheet_ciphers=bool(payload.get("require_sheet_ciphers", True)),
        )


@dataclass(frozen=True)
class PackageCompletenessReport:
    """Outcome of one package-completeness assessment."""

    issues: tuple[ValidationIssue, ...]
    missing_pd_sections: tuple[str, ...] = ()
    unpaired_pd_sections: tuple[str, ...] = ()
    unsupported_formats: tuple[str, ...] = ()
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
                        "native DWG analysis is not implemented — use IFC/PDF/DXF "
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
            disc = artifact.discipline or artifact.section_code
            if disc:
                code = canonicalize_discipline(disc).code
                folded = cipher.casefold()
                # Accept either Latin canonical or common RU aliases in cipher.
                aliases = {code.casefold(), disc.casefold()}
                if code == "AR":
                    aliases.add("ар")
                if code == "KZH":
                    aliases.update({"кж", "кж0"})
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

    # Stable ordering for determinism.
    issues.sort(key=lambda item: (item.rule_id, item.target_ref or "", item.message))
    return PackageCompletenessReport(
        issues=tuple(issues),
        missing_pd_sections=tuple(missing_pd),
        unpaired_pd_sections=tuple(unpaired_pd),
        unsupported_formats=tuple(sorted(set(unsupported))),
    )


def _section_disciplines(
    artifacts: Sequence[PackageArtifact],
    *,
    role: ArtifactRole,
) -> set[str]:
    codes: set[str] = set()
    for artifact in artifacts:
        if artifact.role != role:
            continue
        raw = artifact.section_code or artifact.discipline
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
