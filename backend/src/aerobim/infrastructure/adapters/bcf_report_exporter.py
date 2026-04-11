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

import io
import zipfile
from dataclasses import dataclass
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

from aerobim.domain.models import ClashResult, Severity, ValidationReport

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


def _collect_topics(report: ValidationReport) -> list[_BcfTopicPayload]:
    topics: list[_BcfTopicPayload] = []

    for issue in report.issues:
        if issue.severity != Severity.ERROR:
            continue
        reference_links = tuple(link for link in (issue.element_guid,) if link)
        selected_guids = reference_links
        topics.append(
            _BcfTopicPayload(
                topic_guid=str(uuid4()),
                viewpoint_guid=str(uuid4()),
                title=issue.rule_id or "Validation Issue",
                description=issue.message or "",
                creation_date=report.created_at,
                creation_author="aerobim-backend",
                reference_links=reference_links,
                selected_guids=selected_guids,
                topic_type="Error",
            )
        )

    for index, clash in enumerate(report.clash_results, start=1):
        topics.append(_clash_topic_payload(report, clash, index))

    return topics


def _clash_topic_payload(
    report: ValidationReport,
    clash: ClashResult,
    index: int,
) -> _BcfTopicPayload:
    return _BcfTopicPayload(
        topic_guid=str(uuid4()),
        viewpoint_guid=str(uuid4()),
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
