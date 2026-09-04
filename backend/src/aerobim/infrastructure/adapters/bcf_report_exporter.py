"""BCF XML report exporter.

Converts a ``ValidationReport`` into a minimal BCF 2.1 XML ZIP archive
(buildingSMART BCF-XML schema, ISO 16739-based).

Each ``ValidationIssue`` with severity ERROR becomes a BCF Topic (markup.bcf).
Detected clashes are exported as additional BCF topics in deterministic triage
order (band → severity metric → pair key; see ``domain.clash_triage``) so
coordination tools can consume them directly. Topic child-element order follows
the official ``markup.xsd`` (release_2_1) sequence: ReferenceLink*, Title,
Priority?, Index?, Labels*, CreationDate, CreationAuthor, Description?.
Official 2.1 XSDs declare no targetNamespace, so markup/version/visinfo are
emitted without namespaces (matches buildingSMART sample files and enables
local XSD validation against vendored ``samples/bcf-xsd/release_2_1``).

The archive structure follows::

    bcf.version
    <guid>/
        markup.bcf
        viewpoint.bcfv

The exporter emits a minimal orthogonal viewpoint per topic. Snapshots remain
optional and are intentionally omitted here.
"""

from __future__ import annotations

import hashlib
import io
import uuid
import zipfile
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring

from aerobim.domain.clash_triage import TriagedClash, triage_clash_results
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
)


@dataclass(frozen=True)
class _BcfTopicPayload:
    topic_guid: str
    viewpoint_guid: str
    title: str
    description: str
    creation_date: str
    creation_author: str
    reference_links: tuple[str, ...]
    selected_guids: tuple[str, ...]
    topic_type: str
    topic_status: str = "Open"
    labels: tuple[str, ...] = ()
    priority: str | None = None
    """BCF Topic/Priority text (e.g. triage band Critical/Major/Minor)."""
    topic_index: int | None = None
    """BCF Topic/Index sort order (deterministic triage rank for clashes)."""


def _stable_uuid(seed: str) -> str:
    """Deterministic UUID from seed (BCF Guid fields require UUID form)."""

    digest = hashlib.sha256(f"aerobim:bcf:{seed}".encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


def bcf_topic_zip_dir(topic_guid: str) -> str:
    """Canonical UUID directory name; reject path separators (HD2-BCF-01)."""

    try:
        return str(uuid.UUID(str(topic_guid)))
    except ValueError as exc:
        raise ValueError(f"BCF topic guid is not a UUID: {topic_guid!r}") from exc


def export_bcf(report: ValidationReport) -> bytes:
    """Return a BCF 2.1 ZIP archive as raw bytes."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", _bcf_version_xml())

        for topic in _collect_topics(report):
            topic_dir = bcf_topic_zip_dir(topic.topic_guid)
            zf.writestr(f"{topic_dir}/", "")
            zf.writestr(f"{topic_dir}/markup.bcf", _build_markup(topic))
            zf.writestr(f"{topic_dir}/viewpoint.bcfv", _build_viewpoint(topic))

    return buf.getvalue()


def _bcf_version_xml() -> str:
    # version.xsd (release_2_1): no targetNamespace; VersionId attr + DetailedVersion.
    root = Element("Version", VersionId="2.1")
    SubElement(root, "DetailedVersion").text = "2.1"
    return _to_xml_str(root)


def collect_bcf_topics(report: ValidationReport) -> list[_BcfTopicPayload]:
    """Public topic enumeration shared by BCF ZIP export and BCF API push."""
    return _collect_topics(report)


def _collect_topics(report: ValidationReport) -> list[_BcfTopicPayload]:
    topics: list[_BcfTopicPayload] = []

    for issue in report.issues:
        if not _should_export_issue_as_bcf_topic(issue):
            continue

        reference_links = tuple(
            link
            for link in (
                issue.element_guid,
                issue.target_ref,
                *(issue.evidence_refs or ()),
            )
            if link
        )
        selected_guids: tuple[str, ...] = (issue.element_guid,) if issue.element_guid else ()
        rule_upper = (issue.rule_id or "").upper()
        is_mep = rule_upper.startswith("AEROBIM-MEP-")
        claim_lines = tuple(
            ref for ref in (issue.evidence_refs or ()) if str(ref).startswith("claim_boundary:")
        )
        is_template_or_unverified = (
            rule_upper
            in {
                "AEROBIM-MEP-TEMPLATE",
                "AEROBIM-MEP-UNCLASSIFIED",
                "AEROBIM-MEP-FINDING",
            }
            or any("NOT_VERIFIED" in str(ref) or "synthetic" in str(ref) for ref in claim_lines)
            or issue.severity != Severity.ERROR
        )
        if is_mep:
            mep_guids = tuple(
                ref
                for ref in (issue.evidence_refs or ())
                if isinstance(ref, str)
                and len(ref) == 22
                and not ref.startswith(("mep:", "claim_boundary:"))
            )
            if mep_guids:
                selected_guids = mep_guids
            # Only customer ERROR with geometry may be Clash; else Comment + claim boundary.
            topic_type = (
                "Clash"
                if rule_upper == "AEROBIM-MEP-FORBIDDEN" and not is_template_or_unverified
                else "Comment"
            )
        else:
            topic_type = "Error" if issue.severity == Severity.ERROR else "CoordinationWarning"
        base_description = issue.remark.body if issue.remark is not None else (issue.message or "")
        ai_generated = bool(issue.remark is not None and issue.remark.ai_generated)
        provenance_lines = [
            f"finding_id={issue.finding_id}" if issue.finding_id else None,
            f"source_id={issue.source_id}" if issue.source_id else None,
            (f"evidence_refs={','.join(issue.evidence_refs)}" if issue.evidence_refs else None),
            f"origin={issue.origin}" if issue.origin else None,
            f"ifc_globalid={issue.element_guid}" if issue.element_guid else None,
            (
                "norm="
                + " · ".join(
                    part
                    for part in (issue.norm_source, issue.norm_edition, issue.norm_clause)
                    if part and str(part).strip()
                )
                if any(
                    part and str(part).strip()
                    for part in (issue.norm_source, issue.norm_edition, issue.norm_clause)
                )
                else "norm="
            ),
            "ai_generated=true;expert_confirmation_required=true" if ai_generated else None,
            "claim_boundary:RT-003_OPEN;MEP_not_delivered;geometry_may_be_NOT_VERIFIED"
            if is_mep
            else None,
        ]
        description = base_description
        extras = [line for line in provenance_lines if line]
        if extras:
            description = f"{base_description}\n\n" + "\n".join(extras)
        title = issue.rule_id or "Validation Issue"
        if issue.priority:
            title = f"[P{issue.priority}] {title}"
        seed = issue.finding_id or f"{issue.rule_id}|{issue.element_guid}|{issue.target_ref}"
        labels = tuple(
            label
            for label in (
                f"origin:{issue.origin}" if issue.origin else None,
                f"category:{issue.category.value}" if issue.category else None,
                "ai_generated:true" if ai_generated else None,
                "mep:system-clash" if is_mep else None,
                "mep:not_verified" if is_mep and is_template_or_unverified else None,
            )
            if label
        )
        topics.append(
            _BcfTopicPayload(
                topic_guid=_stable_uuid(f"topic:{seed}"),
                viewpoint_guid=_stable_uuid(f"viewpoint:{seed}"),
                title=title,
                description=description,
                creation_date=report.created_at,
                creation_author="aerobim-backend",
                reference_links=reference_links,
                selected_guids=selected_guids,
                topic_type=topic_type,
                labels=labels,
            )
        )

    for item in triage_clash_results(report.clash_results).items:
        topics.append(_clash_topic_payload(report, item))

    return topics


def _should_export_issue_as_bcf_topic(issue: ValidationIssue) -> bool:
    if issue.severity == Severity.ERROR:
        return True

    rule_id = (issue.rule_id or "").upper()
    # MEP system-pair findings (even WARNING/unclassified) are coordination topics.
    if rule_id.startswith("AEROBIM-MEP-"):
        return True

    # OpenRebar cross-document warnings are actionable coordination findings.
    if issue.severity != Severity.WARNING:
        return False

    return issue.category == FindingCategory.CROSS_DOCUMENT and rule_id.startswith("OPENREBAR-")


def _clash_topic_payload(
    report: ValidationReport,
    item: TriagedClash,
) -> _BcfTopicPayload:
    clash = item.clash
    pair_a, pair_b = item.pair_key
    # Pair-key seed keeps topic GUIDs stable across engine output reorderings.
    seed = f"clash:{pair_a}|{pair_b}|{clash.clash_type}"
    return _BcfTopicPayload(
        topic_guid=_stable_uuid(f"topic:{seed}"),
        viewpoint_guid=_stable_uuid(f"viewpoint:{seed}"),
        title=f"Clash {item.rank}: {clash.clash_type} [{item.band.value}]",
        description=(
            f"{clash.description}. "
            f"Distance: {clash.distance:.6f} m. "
            f"Elements: {clash.element_a_guid}, {clash.element_b_guid}.\n\n"
            f"triage:{item.rationale}\n"
            f"triage:duplicates_merged={item.duplicates_merged}"
        ),
        creation_date=report.created_at,
        creation_author="aerobim-backend",
        reference_links=(clash.element_a_guid, clash.element_b_guid),
        selected_guids=(clash.element_a_guid, clash.element_b_guid),
        topic_type="Clash",
        labels=(
            "origin:deterministic",
            "category:spatial",
            f"triage:band={item.band.value}",
        ),
        priority=item.band.value.capitalize(),
        topic_index=item.rank,
    )


def _build_markup(topic: _BcfTopicPayload) -> str:
    root = Element("Markup")

    topic_node = SubElement(
        root,
        "Topic",
        Guid=topic.topic_guid,
        TopicType=topic.topic_type,
        TopicStatus=topic.topic_status,
    )
    # markup.xsd (release_2_1) Topic sequence: ReferenceLink*, Title, Priority?,
    # Index?, Labels*, CreationDate, CreationAuthor, ..., Description?.
    for reference_link in topic.reference_links:
        SubElement(topic_node, "ReferenceLink").text = reference_link
    SubElement(topic_node, "Title").text = topic.title
    if topic.priority:
        SubElement(topic_node, "Priority").text = topic.priority
    if topic.topic_index is not None:
        SubElement(topic_node, "Index").text = str(topic.topic_index)
    for label in topic.labels:
        SubElement(topic_node, "Labels").text = label
    SubElement(topic_node, "CreationDate").text = topic.creation_date
    SubElement(topic_node, "CreationAuthor").text = topic.creation_author
    SubElement(topic_node, "Description").text = topic.description

    # markup.xsd: Viewpoints is a ViewPoint-typed element with Guid attribute.
    viewpoint = SubElement(root, "Viewpoints", Guid=topic.viewpoint_guid)
    SubElement(viewpoint, "Viewpoint").text = "viewpoint.bcfv"
    SubElement(viewpoint, "Index").text = "0"

    return _to_xml_str(root)


def _build_viewpoint(topic: _BcfTopicPayload) -> str:
    root = Element("VisualizationInfo", Guid=topic.viewpoint_guid)

    # visinfo.xsd (release_2_1) Components: ViewSetupHints?, Selection?,
    # Visibility (required), Coloring?. Empty Selection/Coloring are invalid
    # (both require >=1 child), so they are emitted only when populated.
    components = SubElement(root, "Components")
    if topic.selected_guids:
        selection = SubElement(components, "Selection")
        for ifc_guid in topic.selected_guids:
            SubElement(selection, "Component", IfcGuid=ifc_guid)
    SubElement(components, "Visibility", DefaultVisibility="true")

    # OrthogonalCamera (release_2_1): no AspectRatio element (3.0-only).
    camera = SubElement(root, "OrthogonalCamera")
    _vector_node(camera, "CameraViewPoint", 10.0, 10.0, 10.0)
    _vector_node(camera, "CameraDirection", -0.577350269, -0.577350269, -0.577350269)
    _vector_node(camera, "CameraUpVector", 0.0, 0.0, 1.0)
    SubElement(camera, "ViewToWorldScale").text = "10.0"

    SubElement(root, "ClippingPlanes")
    return _to_xml_str(root)


def _vector_node(parent: Element, name: str, x: float, y: float, z: float) -> None:
    vector = SubElement(parent, name)
    SubElement(vector, "X").text = str(x)
    SubElement(vector, "Y").text = str(y)
    SubElement(vector, "Z").text = str(z)


def _to_xml_str(element: Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(element, encoding="unicode")
