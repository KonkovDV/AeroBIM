"""BCF XML report exporter.

Converts a ``ValidationReport`` into a minimal BCF 2.1 XML ZIP archive
(buildingSMART BCF-XML schema, ISO 16739-based).

Each ``ValidationIssue`` with severity ERROR becomes a BCF Topic (markup.bcf).
Detected clashes are exported as additional BCF topics so coordination tools
can consume them directly.

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

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
)

_BCF_MARKUP_NS = "http://www.buildingsmart-tech.org/bcf/markup/2.1"
_BCF_VERSION_NS = "http://www.buildingsmart-tech.org/bcf/version/2.1"
_BCF_VISINFO_NS = "http://www.buildingsmart-tech.org/bcf/visinfo/2.1"


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


def _stable_uuid(seed: str) -> str:
    """Deterministic UUID from seed (BCF Guid fields require UUID form)."""

    digest = hashlib.sha256(f"aerobim:bcf:{seed}".encode()).hexdigest()
    return str(uuid.UUID(digest[:32]))


def export_bcf(report: ValidationReport) -> bytes:
    """Return a BCF 2.1 ZIP archive as raw bytes."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", _bcf_version_xml())

        for topic in _collect_topics(report):
            zf.writestr(f"{topic.topic_guid}/", "")
            zf.writestr(f"{topic.topic_guid}/markup.bcf", _build_markup(topic))
            zf.writestr(f"{topic.topic_guid}/viewpoint.bcfv", _build_viewpoint(topic))

    return buf.getvalue()


def _bcf_version_xml() -> str:
    root = Element("Version", VersionId="2.1", xmlns=_BCF_VERSION_NS)
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
        selected_guids = (issue.element_guid,) if issue.element_guid else ()
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
        provenance_lines = [
            f"finding_id={issue.finding_id}" if issue.finding_id else None,
            f"source_id={issue.source_id}" if issue.source_id else None,
            (f"evidence_refs={','.join(issue.evidence_refs)}" if issue.evidence_refs else None),
            f"origin={issue.origin}" if issue.origin else None,
            f"ifc_globalid={issue.element_guid}" if issue.element_guid else None,
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

    for index, clash in enumerate(report.clash_results, start=1):
        topics.append(_clash_topic_payload(report, clash, index))

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
    clash: ClashResult,
    index: int,
) -> _BcfTopicPayload:
    seed = f"clash:{clash.element_a_guid}|{clash.element_b_guid}|{clash.clash_type}|{index}"
    return _BcfTopicPayload(
        topic_guid=_stable_uuid(f"topic:{seed}"),
        viewpoint_guid=_stable_uuid(f"viewpoint:{seed}"),
        title=f"Clash {index}: {clash.clash_type}",
        description=(
            f"{clash.description}. "
            f"Distance: {clash.distance:.6f} m. "
            f"Elements: {clash.element_a_guid}, {clash.element_b_guid}."
        ),
        creation_date=report.created_at,
        creation_author="aerobim-backend",
        reference_links=(clash.element_a_guid, clash.element_b_guid),
        selected_guids=(clash.element_a_guid, clash.element_b_guid),
        topic_type="Clash",
        labels=("origin:deterministic", "category:spatial"),
    )


def _build_markup(topic: _BcfTopicPayload) -> str:
    root = Element("Markup", xmlns=_BCF_MARKUP_NS)

    topic_node = SubElement(
        root,
        "Topic",
        Guid=topic.topic_guid,
        TopicType=topic.topic_type,
        TopicStatus=topic.topic_status,
    )
    SubElement(topic_node, "Title").text = topic.title
    SubElement(topic_node, "Description").text = topic.description
    SubElement(topic_node, "CreationDate").text = topic.creation_date
    SubElement(topic_node, "CreationAuthor").text = topic.creation_author
    if topic.labels:
        for label in topic.labels:
            SubElement(topic_node, "Labels").text = label

    for reference_link in topic.reference_links:
        SubElement(topic_node, "ReferenceLink").text = reference_link

    viewpoints = SubElement(root, "Viewpoints")
    viewpoint = SubElement(viewpoints, "Viewpoint", Guid=topic.viewpoint_guid)
    SubElement(viewpoint, "Viewpoint").text = "viewpoint.bcfv"
    SubElement(viewpoint, "Index").text = "0"

    return _to_xml_str(root)


def _build_viewpoint(topic: _BcfTopicPayload) -> str:
    root = Element("VisualizationInfo", Guid=topic.viewpoint_guid, xmlns=_BCF_VISINFO_NS)

    components = SubElement(root, "Components")
    selection = SubElement(components, "Selection")
    for ifc_guid in topic.selected_guids:
        SubElement(selection, "Component", IfcGuid=ifc_guid)

    SubElement(components, "Visibility", DefaultVisibility="true")
    SubElement(components, "Coloring")

    camera = SubElement(root, "OrthogonalCamera")
    _vector_node(camera, "CameraViewPoint", 10.0, 10.0, 10.0)
    _vector_node(camera, "CameraDirection", -0.577350269, -0.577350269, -0.577350269)
    _vector_node(camera, "CameraUpVector", 0.0, 0.0, 1.0)
    SubElement(camera, "ViewToWorldScale").text = "10.0"
    SubElement(camera, "AspectRatio").text = "1.7777777777777777"

    SubElement(root, "ClippingPlanes")
    return _to_xml_str(root)


def _vector_node(parent: Element, name: str, x: float, y: float, z: float) -> None:
    vector = SubElement(parent, name)
    SubElement(vector, "X").text = str(x)
    SubElement(vector, "Y").text = str(y)
    SubElement(vector, "Z").text = str(z)


def _to_xml_str(element: Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(element, encoding="unicode")
