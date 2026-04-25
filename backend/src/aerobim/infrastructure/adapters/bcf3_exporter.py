"""BCF 3.0 XML report exporter (experimental).

Converts a ``ValidationReport`` into a BCF 3.0 ZIP archive following the
buildingSMART BCF-XML 3.0 schema.

Key differences from BCF 2.1 (implemented in bcf_report_exporter.py):

* ``bcf.version`` VersionId = ``"3.0"``, DetailedVersion = ``"3.0"``.
* ``markup.bcf`` root element is ``<Markup>`` with no XML namespace; attributes
  use camelCase per BCF 3.0 XSD.
* ``Topic`` uses new required fields: ``Guid``, ``TopicType``, ``TopicStatus``,
  ``Title``, ``CreationDate``, ``CreationAuthor``, ``ModifiedDate``,
  ``ModifiedAuthor``, ``Description``.
* ``Comment`` block included per topic (BCF 3.0 requires at least an empty list).
* ``Viewpoint`` reference in ``Viewpoints`` uses ``Guid`` attribute (3.0 style).
* ``viewpoint.bcfv`` root element is ``VisualizationInfo`` with ``Guid``
  attribute; ``Components.Selection.Component`` uses ``IfcGuid`` attribute as
  in 2.1 but ``Coloring`` and ``Visibility`` child structure is updated per 3.0
  XSD (``Coloring`` before ``Visibility``).
* No XML namespace declarations on markup and visinfo (3.0 dropped them).

The exporter is intentionally minimal and experimental.  It is not a full BCF 3.0
implementation (BCF API, extensions.xml, document references are out of scope).

Public API:
    export_bcf3(report: ValidationReport) -> bytes
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

from aerobim.domain.models import (
    ClashResult,
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationReport,
)

_BCF30_VERSION = "3.0"


@dataclass(frozen=True)
class _Bcf3TopicPayload:
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


def export_bcf3(report: ValidationReport) -> bytes:
    """Return a BCF 3.0 ZIP archive as raw bytes."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", _bcf3_version_xml())

        for topic in _collect_topics(report):
            zf.writestr(f"{topic.topic_guid}/", "")
            zf.writestr(f"{topic.topic_guid}/markup.bcf", _build_markup3(topic))
            zf.writestr(
                f"{topic.topic_guid}/viewpoint.bcfv",
                _build_viewpoint3(topic),
            )

    return buf.getvalue()


def _bcf3_version_xml() -> str:
    root = Element("Version", VersionId=_BCF30_VERSION)
    SubElement(root, "DetailedVersion").text = _BCF30_VERSION
    return _to_xml_str(root)


def _collect_topics(report: ValidationReport) -> list[_Bcf3TopicPayload]:
    topics: list[_Bcf3TopicPayload] = []

    for issue in report.issues:
        if not _should_export(issue):
            continue

        reference_links = tuple(link for link in (issue.element_guid, issue.target_ref) if link)
        selected_guids = (issue.element_guid,) if issue.element_guid else ()
        topic_type = "Error" if issue.severity == Severity.ERROR else "Warning"
        topics.append(
            _Bcf3TopicPayload(
                topic_guid=str(uuid4()),
                viewpoint_guid=str(uuid4()),
                title=issue.rule_id or "Validation Issue",
                description=issue.message or "",
                creation_date=report.created_at,
                creation_author="aerobim-backend",
                reference_links=reference_links,
                selected_guids=selected_guids,
                topic_type=topic_type,
            )
        )

    for index, clash in enumerate(report.clash_results, start=1):
        topics.append(_clash_topic(report, clash, index))

    return topics


def _should_export(issue: ValidationIssue) -> bool:
    if issue.severity == Severity.ERROR:
        return True
    if issue.severity != Severity.WARNING:
        return False
    rule_id = (issue.rule_id or "").upper()
    return issue.category == FindingCategory.CROSS_DOCUMENT and rule_id.startswith("OPENREBAR-")


def _clash_topic(
    report: ValidationReport,
    clash: ClashResult,
    index: int,
) -> _Bcf3TopicPayload:
    return _Bcf3TopicPayload(
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


def _build_markup3(topic: _Bcf3TopicPayload) -> str:
    """Build BCF 3.0 markup.bcf XML (no namespace)."""
    root = Element("Markup")

    header = SubElement(root, "Header")
    SubElement(header, "File", Date=topic.creation_date)

    topic_node = SubElement(
        root,
        "Topic",
        Guid=topic.topic_guid,
        TopicType=topic.topic_type,
        TopicStatus=topic.topic_status,
    )
    SubElement(topic_node, "Title").text = topic.title
    SubElement(topic_node, "CreationDate").text = topic.creation_date
    SubElement(topic_node, "CreationAuthor").text = topic.creation_author
    SubElement(topic_node, "ModifiedDate").text = topic.creation_date
    SubElement(topic_node, "ModifiedAuthor").text = topic.creation_author
    SubElement(topic_node, "Description").text = topic.description

    for link in topic.reference_links:
        SubElement(topic_node, "ReferenceLink").text = link

    # BCF 3.0: Comments list (may be empty)
    SubElement(root, "Comments")

    # BCF 3.0: Viewpoints list
    viewpoints = SubElement(root, "Viewpoints")
    vp = SubElement(viewpoints, "ViewPoint", Guid=topic.viewpoint_guid)
    SubElement(vp, "Viewpoint").text = "viewpoint.bcfv"
    SubElement(vp, "Index").text = "0"

    return _to_xml_str(root)


def _build_viewpoint3(topic: _Bcf3TopicPayload) -> str:
    """Build BCF 3.0 viewpoint.bcfv XML (no namespace)."""
    root = Element("VisualizationInfo", Guid=topic.viewpoint_guid)

    components = SubElement(root, "Components")
    # BCF 3.0 XSD: Coloring before Visibility
    SubElement(components, "Coloring")

    selection = SubElement(components, "Selection")
    for ifc_guid in topic.selected_guids:
        SubElement(selection, "Component", IfcGuid=ifc_guid)

    SubElement(components, "Visibility", DefaultVisibility="true")

    camera = SubElement(root, "OrthogonalCamera")
    _vector(camera, "CameraViewPoint", 10.0, 10.0, 10.0)
    _vector(camera, "CameraDirection", -0.577350269, -0.577350269, -0.577350269)
    _vector(camera, "CameraUpVector", 0.0, 0.0, 1.0)
    SubElement(camera, "ViewToWorldScale").text = "10.0"
    SubElement(camera, "AspectRatio").text = "1.7777777777777777"

    SubElement(root, "ClippingPlanes")
    return _to_xml_str(root)


def _vector(parent: Element, name: str, x: float, y: float, z: float) -> None:
    node = SubElement(parent, name)
    SubElement(node, "X").text = str(x)
    SubElement(node, "Y").text = str(y)
    SubElement(node, "Z").text = str(z)


def _to_xml_str(element: Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(element, encoding="unicode")
