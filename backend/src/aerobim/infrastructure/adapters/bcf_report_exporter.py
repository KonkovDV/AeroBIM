"""BCF XML report exporter.

Converts a ``ValidationReport`` into a minimal BCF 2.1 XML ZIP archive
(buildingSMART BCF-XML schema, ISO 16739-based).

Each ``ValidationIssue`` with severity ERROR becomes a BCF Topic (markup.bcf).
The archive structure follows::

    bcf.version
    <guid>/
        markup.bcf

No viewpoints or snapshots are included in this minimal baseline.
"""

from __future__ import annotations

import io
import zipfile
from uuid import uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

from aerobim.domain.models import Severity, ValidationIssue, ValidationReport


def export_bcf(report: ValidationReport) -> bytes:
    """Return a BCF 2.1 ZIP archive as raw bytes."""
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", _bcf_version_xml())

        error_issues = [
            issue for issue in report.issues if issue.severity == Severity.ERROR
        ]
        for issue in error_issues:
            topic_guid = uuid4().hex
            markup = _build_markup(topic_guid, issue, report)
            zf.writestr(f"{topic_guid}/markup.bcf", markup)

    return buf.getvalue()


def _bcf_version_xml() -> str:
    root = Element("Version", VersionId="2.1", xmlns="http://www.buildingsmart-tech.org/bcf/version/2.1")
    SubElement(root, "DetailedVersion").text = "2.1"
    return _to_xml_str(root)


def _build_markup(topic_guid: str, issue: ValidationIssue, report: ValidationReport) -> str:
    root = Element("Markup", xmlns="http://www.buildingsmart-tech.org/bcf/markup/2.1")

    topic = SubElement(root, "Topic", Guid=topic_guid, TopicType="Error", TopicStatus="Open")
    SubElement(topic, "Title").text = issue.rule_id or "Validation Issue"
    SubElement(topic, "Description").text = issue.message or ""
    SubElement(topic, "CreationDate").text = report.created_at
    SubElement(topic, "CreationAuthor").text = "aerobim-backend"

    if issue.element_guid:
        SubElement(topic, "ReferenceLink").text = issue.element_guid

    return _to_xml_str(root)


def _to_xml_str(element: Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(element, encoding="unicode")
