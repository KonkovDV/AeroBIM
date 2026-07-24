"""MEP system-aware clash domain (MEP-CLASH-001 / RT-003) — engineering foundation.

Do not claim Solibri/Navisworks replacement. Default DI remains
``UnconfiguredMepSystemGraphProvider`` (fail-closed → NOT_VERIFIED / BLOCKED under
``require_mep``). Synthetic providers are unit-test only and never grant OK capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

MepExceptionKind = Literal[
    "sleeve",
    "insulation",
    "same_system",
    "intentional_containment",
]

MepIntersectionVerdict = Literal["allowed", "forbidden", "unclassified"]


class MepClearanceClass(StrEnum):
    HARD = "hard"
    SOFT = "soft"
    ADVISORY = "advisory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MepSystem:
    """Named MEP system with discipline and provenance."""

    system_id: str
    system_type: str
    discipline: str
    source_ifc: str | None = None
    element_guids: tuple[str, ...] = ()
    priority: int = 0


@dataclass(frozen=True)
class MepSystemNode:
    """Legacy graph node; prefer ``MepSystem`` for new call sites."""

    system_id: str
    system_type: str
    element_guids: tuple[str, ...]
    discipline: str = "MEP"
    source_ifc: str | None = None


@dataclass(frozen=True)
class MepSystemGraph:
    """Connectivity graph derived from IFC system assignments."""

    nodes: tuple[MepSystemNode, ...]
    edges: tuple[tuple[str, str], ...]
    """Undirected pairs of system_id connected via shared elements / ports."""
    source_ifc: str | None = None
    synthetic: bool = False
    """True when built by a synthetic/@sota-stub provider — never product evidence."""


@dataclass(frozen=True)
class MepClearanceRule:
    """Single allowed/forbidden intersection row with clearance semantics."""

    system_a: str
    system_b: str
    allowed_intersection: bool
    clearance_class: MepClearanceClass = MepClearanceClass.UNKNOWN
    min_clearance_m: float | None = None
    priority: int = 0
    exception_kinds: tuple[MepExceptionKind, ...] = ()
    notes: str | None = None
    discipline_a: str | None = None
    discipline_b: str | None = None
    system_type_a: str | None = None
    system_type_b: str | None = None


@dataclass(frozen=True)
class MepClashMatrix:
    """Customer or template clearance / intersection matrix."""

    rules: tuple[MepClearanceRule, ...]
    scope_memo_ref: str | None = None
    units: str = "m"
    default_clearance_m: float | None = None
    claim_boundary: str | None = None
    synthetic: bool = False


@dataclass(frozen=True)
class AllowedIntersectionRule:
    """Back-compat alias shape used by earlier scaffolds."""

    system_a: str
    system_b: str
    allowed: bool
    min_clearance_m: float | None = None
    requires_insulation_gap: bool = False
    notes: str | None = None


@dataclass(frozen=True)
class AllowedIntersectionMatrix:
    rules: tuple[AllowedIntersectionRule, ...]


@dataclass(frozen=True)
class MepClashFinding:
    """System-aware clash finding with full provenance (never empty-as-OK)."""

    finding_id: str
    system_a: str
    system_b: str
    verdict: MepIntersectionVerdict
    message: str
    discipline_a: str | None = None
    discipline_b: str | None = None
    system_type_a: str | None = None
    system_type_b: str | None = None
    source_ifc: str | None = None
    element_guid_a: str | None = None
    element_guid_b: str | None = None
    clearance_class: MepClearanceClass = MepClearanceClass.UNKNOWN
    allowed_intersection: bool | None = None
    priority: int = 0
    exception_kinds: tuple[MepExceptionKind, ...] = ()
    min_clearance_m: float | None = None
    capability_hint: Literal["error", "not_verified", "info"] = "error"


def _pair_key(system_a: str, system_b: str) -> tuple[str, str]:
    left, right = sorted((system_a.strip(), system_b.strip()), key=str.casefold)
    return left, right


def lookup_clearance_rule(
    matrix: MepClashMatrix,
    system_a: str,
    system_b: str,
) -> MepClearanceRule | None:
    key = _pair_key(system_a, system_b)
    for rule in matrix.rules:
        if _pair_key(rule.system_a, rule.system_b) == key:
            return rule
    return None


def evaluate_system_pair(
    *,
    system_a: MepSystem | MepSystemNode,
    system_b: MepSystem | MepSystemNode,
    matrix: MepClashMatrix,
    source_ifc: str | None = None,
    intersecting: bool = True,
) -> MepClashFinding | None:
    """Evaluate one system pair against the clearance matrix.

    - allowed intersection → no finding (``None``)
    - forbidden intersection → finding with provenance (capability_hint=error)
    - unclassified pair → NOT_VERIFIED-shaped finding (never confident ERROR)
    """

    if not intersecting:
        return None

    a_id = system_a.system_id
    b_id = system_b.system_id
    if a_id == b_id:
        return None

    discipline_a = getattr(system_a, "discipline", None)
    discipline_b = getattr(system_b, "discipline", None)
    type_a = system_a.system_type
    type_b = system_b.system_type
    guids_a = getattr(system_a, "element_guids", ())
    guids_b = getattr(system_b, "element_guids", ())
    ifc = source_ifc or getattr(system_a, "source_ifc", None) or matrix.scope_memo_ref

    rule = lookup_clearance_rule(matrix, a_id, b_id)
    if rule is None:
        return MepClashFinding(
            finding_id=f"mep-unclassified-{a_id}-{b_id}",
            system_a=a_id,
            system_b=b_id,
            verdict="unclassified",
            message=(
                f"System pair {a_id!r}↔{b_id!r} has no matrix row — "
                "NOT_VERIFIED (not a confident ERROR); RT-003 open"
            ),
            discipline_a=discipline_a,
            discipline_b=discipline_b,
            system_type_a=type_a,
            system_type_b=type_b,
            source_ifc=ifc,
            element_guid_a=guids_a[0] if guids_a else None,
            element_guid_b=guids_b[0] if guids_b else None,
            clearance_class=MepClearanceClass.UNKNOWN,
            allowed_intersection=None,
            priority=0,
            capability_hint="not_verified",
        )

    if rule.allowed_intersection:
        return None

    return MepClashFinding(
        finding_id=f"mep-forbidden-{a_id}-{b_id}",
        system_a=a_id,
        system_b=b_id,
        verdict="forbidden",
        message=(
            f"Forbidden intersection {a_id!r}↔{b_id!r} "
            f"(clearance_class={rule.clearance_class.value}; "
            f"priority={rule.priority})"
        ),
        discipline_a=discipline_a or rule.discipline_a,
        discipline_b=discipline_b or rule.discipline_b,
        system_type_a=type_a or rule.system_type_a,
        system_type_b=type_b or rule.system_type_b,
        source_ifc=ifc,
        element_guid_a=guids_a[0] if guids_a else None,
        element_guid_b=guids_b[0] if guids_b else None,
        clearance_class=rule.clearance_class,
        allowed_intersection=False,
        priority=rule.priority,
        exception_kinds=rule.exception_kinds,
        min_clearance_m=rule.min_clearance_m,
        capability_hint="error",
    )


def evaluate_matrix_against_graph(
    graph: MepSystemGraph,
    matrix: MepClashMatrix,
    *,
    intersecting_pairs: set[tuple[str, str]] | None = None,
) -> tuple[MepClashFinding, ...]:
    """Evaluate all undirected system pairs (edges or cartesian of nodes).

    When ``intersecting_pairs`` is provided, only those pairs are treated as
    geometrically intersecting; others are skipped (no finding).
    """

    nodes = {node.system_id: node for node in graph.nodes}
    if intersecting_pairs is not None:
        pairs = {_pair_key(a, b) for a, b in intersecting_pairs}
    elif graph.edges:
        pairs = {_pair_key(a, b) for a, b in graph.edges}
    else:
        ids = sorted(nodes)
        pairs = {_pair_key(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))}

    findings: list[MepClashFinding] = []
    for left, right in sorted(pairs):
        node_a = nodes.get(left)
        node_b = nodes.get(right)
        if node_a is None or node_b is None:
            findings.append(
                MepClashFinding(
                    finding_id=f"mep-missing-node-{left}-{right}",
                    system_a=left,
                    system_b=right,
                    verdict="unclassified",
                    message="Pair references unknown system node — NOT_VERIFIED",
                    source_ifc=graph.source_ifc,
                    capability_hint="not_verified",
                )
            )
            continue
        finding = evaluate_system_pair(
            system_a=node_a,
            system_b=node_b,
            matrix=matrix,
            source_ifc=graph.source_ifc,
            intersecting=True,
        )
        if finding is not None:
            findings.append(finding)
    return tuple(findings)


class MepSystemGraphProvider(Protocol):
    """Build duct/pipe/tray connectivity from IFC system assignments."""

    def build(self, ifc_path: Path) -> MepSystemGraph: ...


class UnconfiguredMepSystemGraphProvider:
    """Fail-closed placeholder until Samolet federated MEP IFC + scope memo exist."""

    def build(self, ifc_path: Path) -> MepSystemGraph:
        del ifc_path
        raise RuntimeError(
            "MEP system graph is not configured (MEP-CLASH-001): "
            "requires federated MEP IFC with systems and a signed scope memo"
        )


class SyntheticMepSystemGraphProvider:
    """Unit-test / scaffold name-pair graph — never product OK capability.

    /** @sota-stub */
    Tagged synthetic: returns a fixed multi-system graph independent of IFC bytes.
    Analyze path must keep ``mep_system_clash=NOT_VERIFIED`` even when nodes exist.
    """

    def __init__(
        self,
        *,
        systems: tuple[MepSystemNode, ...] | None = None,
        edges: tuple[tuple[str, str], ...] | None = None,
    ) -> None:
        self._systems = systems or (
            MepSystemNode(
                system_id="HVAC-SUPPLY",
                system_type="HVAC",
                discipline="OV",
                element_guids=("guid-hvac-1",),
                source_ifc="synthetic",
            ),
            MepSystemNode(
                system_id="SPRINKLER",
                system_type="FIRE",
                discipline="PT",
                element_guids=("guid-spk-1",),
                source_ifc="synthetic",
            ),
            MepSystemNode(
                system_id="CABLE-TRAY",
                system_type="EL",
                discipline="EL",
                element_guids=("guid-el-1",),
                source_ifc="synthetic",
            ),
        )
        self._edges = edges or (
            ("HVAC-SUPPLY", "SPRINKLER"),
            ("HVAC-SUPPLY", "CABLE-TRAY"),
            ("SPRINKLER", "CABLE-TRAY"),
        )

    def build(self, ifc_path: Path) -> MepSystemGraph:
        return MepSystemGraph(
            nodes=self._systems,
            edges=self._edges,
            source_ifc=str(ifc_path),
            synthetic=True,
        )


@dataclass(frozen=True)
class FederatedMepScope:
    """Customer federated MEP scope manifest (RT-003). Empty template stays NOT_VERIFIED.

    ``ENG_FIXTURE`` unlocks engineering graph builds only (synthetic). ``VERIFIED``
    requires customer memo + expert sign-off — never self-attestation alone.
    """

    schema_version: str
    status: str
    federated_ifc_paths: tuple[str, ...]
    scope_memo_ref: str | None
    clearance_matrix_ref: str | None
    claim_boundary: str
    expert_signed_by: str | None = None
    expert_signed_at: str | None = None

    @property
    def eng_fixture(self) -> bool:
        return self.status.upper() in {"ENG_FIXTURE", "ENGINEERING_FIXTURE"}

    @property
    def verified(self) -> bool:
        """True only for customer-signed VERIFIED scopes (RT-003)."""

        return (
            self.status.upper() == "VERIFIED"
            and bool(self.federated_ifc_paths)
            and bool(self.scope_memo_ref)
            and bool(self.expert_signed_by)
            and bool(self.expert_signed_at)
        )

    @property
    def allows_federated_graph(self) -> bool:
        """Customer verified OR engineering fixture with paths."""

        return bool(self.federated_ifc_paths) and (self.verified or self.eng_fixture)


def load_federated_mep_scope(path: Path) -> FederatedMepScope:
    """Load federated MEP scope JSON; refuses to upgrade NOT_VERIFIED without paths."""

    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("federated MEP scope must be a JSON object")
    raw_paths = payload.get("federated_ifc_paths") or []
    if not isinstance(raw_paths, list):
        raise ValueError("federated_ifc_paths must be an array")
    paths = tuple(str(item).strip() for item in raw_paths if str(item).strip())
    status = str(payload.get("status") or "NOT_VERIFIED").strip().upper()
    if status == "VERIFIED" and not paths:
        raise ValueError("VERIFIED federated MEP scope requires federated_ifc_paths")
    signoff = payload.get("expert_signoff")
    signed_by: str | None = None
    signed_at: str | None = None
    if isinstance(signoff, dict):
        signed_by = _optional_str(signoff.get("signed_by"))
        signed_at = _optional_str(signoff.get("signed_at"))
    if status == "VERIFIED" and (not signed_by or not signed_at):
        raise ValueError(
            "VERIFIED federated MEP scope requires expert_signoff.signed_by and signed_at"
        )
    if status == "VERIFIED" and not _optional_str(payload.get("scope_memo_ref")):
        raise ValueError("VERIFIED federated MEP scope requires scope_memo_ref")
    return FederatedMepScope(
        schema_version=str(payload.get("schema_version") or "1.0.0"),
        status=status,
        federated_ifc_paths=paths,
        scope_memo_ref=_optional_str(payload.get("scope_memo_ref")),
        clearance_matrix_ref=_optional_str(payload.get("clearance_matrix_ref")),
        claim_boundary=str(
            payload.get("claim_boundary")
            or "RT-003 remains OPEN until customer federated IFC + signed matrix"
        ),
        expert_signed_by=signed_by,
        expert_signed_at=signed_at,
    )


def load_mep_clearance_matrix(path: Path) -> MepClashMatrix:
    """Load clearance / intersection matrix JSON (template or customer signed).

    Accepts ``pairs[]`` with ``min_clearance_mm`` / ``min_clearance_m`` and
    ``allowed_intersection``. Units default from payload (``mm`` → convert to m).
    """

    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("MEP clearance matrix must be a JSON object")
    units = str(payload.get("units") or "m").strip().lower()
    scale = 0.001 if units in {"mm", "millimetre", "millimeter"} else 1.0
    default_raw = payload.get("default_clearance_m")
    if default_raw is None and payload.get("default_clearance_mm") is not None:
        default_raw = float(payload["default_clearance_mm"]) * 0.001
    elif default_raw is not None:
        default_raw = float(default_raw) * (scale if units != "m" else 1.0)

    raw_pairs = payload.get("pairs") or payload.get("rules") or []
    if not isinstance(raw_pairs, list):
        raise ValueError("MEP clearance matrix pairs must be an array")
    rules: list[MepClearanceRule] = []
    for row in raw_pairs:
        if not isinstance(row, dict):
            continue
        system_a = str(row.get("system_a") or "").strip()
        system_b = str(row.get("system_b") or "").strip()
        if not system_a or not system_b:
            continue
        min_clearance: float | None = None
        if row.get("min_clearance_m") is not None:
            min_clearance = float(row["min_clearance_m"])
        elif row.get("min_clearance_mm") is not None:
            min_clearance = float(row["min_clearance_mm"]) * 0.001
        clearance_raw = str(row.get("clearance_class") or "unknown").strip().lower()
        try:
            clearance_class = MepClearanceClass(clearance_raw)
        except ValueError:
            clearance_class = MepClearanceClass.UNKNOWN
        rules.append(
            MepClearanceRule(
                system_a=system_a,
                system_b=system_b,
                allowed_intersection=bool(row.get("allowed_intersection", False)),
                clearance_class=clearance_class,
                min_clearance_m=min_clearance,
                priority=int(row.get("priority") or 0),
                notes=_optional_str(row.get("note") or row.get("notes")),
            )
        )
    return MepClashMatrix(
        rules=tuple(rules),
        scope_memo_ref=_optional_str(payload.get("scope_memo_ref")),
        units="m",
        default_clearance_m=float(default_raw) if default_raw is not None else None,
        claim_boundary=_optional_str(payload.get("claim_boundary")),
        synthetic=bool(payload.get("synthetic", False))
        or "template" in str(payload.get("claim_boundary") or "").lower(),
    )


def mep_finding_to_issue(
    finding: MepClashFinding,
    *,
    matrix_synthetic: bool = False,
    geometry_verified: bool = False,
):
    """Map domain MEP finding → ValidationIssue (advisory/engine spatial).

    Template/synthetic matrices and co-presence-only graphs never emit ERROR.
    """

    from aerobim.domain.models import FindingCategory, Severity, ValidationIssue

    verdict = finding.verdict
    hint = finding.capability_hint
    message = finding.message
    if not geometry_verified and verdict == "forbidden":
        verdict = "unclassified"
        hint = "not_verified"
        message = (
            f"{finding.message} — co-presence only; geometry intersection NOT_VERIFIED (RT-003)"
        )
    if matrix_synthetic and verdict == "forbidden":
        verdict = "unclassified"
        hint = "not_verified"
        message = f"{finding.message} — template/synthetic matrix (not customer ERROR)"

    if hint == "error" and verdict == "forbidden" and geometry_verified and not matrix_synthetic:
        severity = Severity.ERROR
        rule_id = "AEROBIM-MEP-FORBIDDEN"
    elif matrix_synthetic:
        severity = Severity.WARNING
        rule_id = "AEROBIM-MEP-TEMPLATE"
    elif verdict == "unclassified" or not geometry_verified:
        severity = Severity.WARNING
        rule_id = "AEROBIM-MEP-UNCLASSIFIED"
    else:
        severity = Severity.WARNING
        rule_id = "AEROBIM-MEP-FINDING"

    guids = tuple(guid for guid in (finding.element_guid_a, finding.element_guid_b) if guid)
    return ValidationIssue(
        rule_id=rule_id,
        severity=severity,
        message=message,
        category=FindingCategory.SPATIAL,
        element_guid=finding.element_guid_a,
        target_ref=f"{finding.system_a}|{finding.system_b}",
        source_id=finding.source_ifc or "mep-system-clash",
        finding_id=finding.finding_id,
        evidence_refs=(
            *guids,
            (
                "claim_boundary:geometry_NOT_VERIFIED"
                if not geometry_verified
                else "claim_boundary:geometry_verified"
            ),
            (
                "claim_boundary:matrix_synthetic"
                if matrix_synthetic
                else "claim_boundary:matrix_customer_or_unknown"
            ),
        ),
        origin="deterministic",
    )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
