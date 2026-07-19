"""Independent BCF ZIP consumers for contract tests (read-side only).

Two parsers with intentionally different XML strategies must agree on topic
GUID, title, and viewpoint presence — that is the interoperability seam.

Structural verification follows buildingSMART BCFZIP practice: require
``bcf.version``, ``markup.bcf`` per topic folder, and well-formed XML.
Optional XSD validation runs only when schema files are vendored locally.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class BcfTopicContract:
    topic_guid: str
    title: str
    has_viewpoint: bool
    selected_ifc_guids: tuple[str, ...]


@dataclass(frozen=True)
class BcfStructuralVerification:
    ok: bool
    version_id: str
    topic_count: int
    markup_count: int
    viewpoint_count: int
    sha256: str
    errors: tuple[str, ...]
    xsd_status: str
    """``not_configured`` | ``not_run`` | ``failed`` | ``skipped``.

    Never ``passed`` without an actual XSD validation run.
    """

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def consume_bcf21_zip(archive: bytes) -> list[BcfTopicContract]:
    """Consumer A: namespace-aware ElementTree walk of BCF 2.1 ZIP."""

    topics: list[BcfTopicContract] = []
    with zipfile.ZipFile(io.BytesIO(archive), "r") as zf:
        version_raw = zf.read("bcf.version")
        version_root = ET.fromstring(version_raw)
        version_id = version_root.attrib.get("VersionId", "")
        if version_id and not version_id.startswith("2."):
            raise ValueError(f"BCF 2.1 consumer rejected VersionId={version_id!r}")

        markup_names = sorted(n for n in zf.namelist() if n.endswith("/markup.bcf"))
        for markup_name in markup_names:
            topic_guid = markup_name.split("/", 1)[0]
            root = ET.fromstring(zf.read(markup_name))
            topic_el = _find_local(root, "Topic")
            if topic_el is None:
                raise ValueError(f"markup missing Topic: {markup_name}")
            title_el = _find_local(topic_el, "Title")
            title = (title_el.text or "").strip() if title_el is not None else ""
            viewpoint_name = f"{topic_guid}/viewpoint.bcfv"
            has_viewpoint = viewpoint_name in zf.namelist()
            selected: list[str] = []
            if has_viewpoint:
                vis = ET.fromstring(zf.read(viewpoint_name))
                for component in vis.iter():
                    if _local(component.tag) == "Component":
                        guid = component.attrib.get("IfcGuid") or component.attrib.get("ifc_guid")
                        if guid:
                            selected.append(guid)
            topics.append(
                BcfTopicContract(
                    topic_guid=topic_guid,
                    title=title,
                    has_viewpoint=has_viewpoint,
                    selected_ifc_guids=tuple(selected),
                )
            )
    return topics


def consume_bcf3_zip(archive: bytes) -> list[BcfTopicContract]:
    """Consumer B: string/tag-local scan of BCF 3.0 ZIP (no shared helper with A)."""

    topics: list[BcfTopicContract] = []
    with zipfile.ZipFile(io.BytesIO(archive), "r") as zf:
        version_text = zf.read("bcf.version").decode("utf-8", errors="replace")
        if 'VersionId="3.0"' not in version_text and "VersionId='3.0'" not in version_text:
            # Accept DetailedVersion text fallback.
            if "3.0" not in version_text:
                raise ValueError("BCF 3.0 consumer rejected bcf.version payload")

        for name in sorted(n for n in zf.namelist() if n.endswith("/markup.bcf")):
            topic_guid = name.split("/", 1)[0]
            markup = zf.read(name).decode("utf-8", errors="replace")
            title = _extract_tag_text(markup, "Title")
            viewpoint_name = f"{topic_guid}/viewpoint.bcfv"
            has_viewpoint = viewpoint_name in zf.namelist()
            selected: list[str] = []
            if has_viewpoint:
                vis_xml = zf.read(viewpoint_name).decode("utf-8", errors="replace")
                # BCF 3.0 uses IfcGuid attribute on Component.
                needle = 'IfcGuid="'
                start = 0
                while True:
                    idx = vis_xml.find(needle, start)
                    if idx < 0:
                        break
                    end = vis_xml.find('"', idx + len(needle))
                    if end < 0:
                        break
                    selected.append(vis_xml[idx + len(needle) : end])
                    start = end + 1
            topics.append(
                BcfTopicContract(
                    topic_guid=topic_guid,
                    title=title,
                    has_viewpoint=has_viewpoint,
                    selected_ifc_guids=tuple(selected),
                )
            )
    return topics


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _find_local(root: ET.Element, name: str) -> ET.Element | None:
    for element in root.iter():
        if _local(element.tag) == name:
            return element
    return None


def _extract_tag_text(xml: str, tag: str) -> str:
    open_tag = f"<{tag}"
    start = xml.find(open_tag)
    if start < 0:
        return ""
    gt = xml.find(">", start)
    if gt < 0:
        return ""
    if xml[gt - 1] == "/":
        return ""
    close = xml.find(f"</{tag}>", gt)
    if close < 0:
        return ""
    return xml[gt + 1 : close].strip()


def verify_bcf_zip_structure(
    archive: bytes,
    *,
    xsd_dir: Path | None = None,
) -> BcfStructuralVerification:
    """buildingSMART-style container checks (structure + well-formed XML)."""

    errors: list[str] = []
    digest = hashlib.sha256(archive).hexdigest()
    version_id = ""
    markup_count = 0
    viewpoint_count = 0
    topic_guids: list[str] = []

    try:
        with zipfile.ZipFile(io.BytesIO(archive), "r") as zf:
            names = set(zf.namelist())
            if "bcf.version" not in names:
                errors.append("missing bcf.version")
            else:
                try:
                    root = ET.fromstring(zf.read("bcf.version"))
                    version_id = root.attrib.get("VersionId", "") or ""
                    if not version_id:
                        errors.append("bcf.version missing VersionId")
                except ET.ParseError as exc:
                    errors.append(f"bcf.version not well-formed XML: {exc}")

            markup_names = sorted(n for n in names if n.endswith("/markup.bcf"))
            markup_count = len(markup_names)
            if markup_count == 0:
                errors.append("no markup.bcf entries in archive")

            for markup_name in markup_names:
                topic_guid = markup_name.split("/", 1)[0]
                topic_guids.append(topic_guid)
                try:
                    ET.fromstring(zf.read(markup_name))
                except ET.ParseError as exc:
                    errors.append(f"markup not well-formed: {markup_name}: {exc}")
                viewpoint_name = f"{topic_guid}/viewpoint.bcfv"
                if viewpoint_name in names:
                    viewpoint_count += 1
                    try:
                        ET.fromstring(zf.read(viewpoint_name))
                    except ET.ParseError as exc:
                        errors.append(f"viewpoint not well-formed: {viewpoint_name}: {exc}")
                else:
                    errors.append(f"missing viewpoint.bcfv for topic {topic_guid}")
    except zipfile.BadZipFile as exc:
        errors.append(f"not a ZIP archive: {exc}")

    xsd_status = "not_configured"
    if xsd_dir is not None and xsd_dir.is_dir():
        xsd_files = list(xsd_dir.glob("*.xsd"))
        if not xsd_files:
            xsd_status = "skipped"
        else:
            xsd_status = "not_run"
            # Presence of XSD files does not imply validation ran or failed.

    return BcfStructuralVerification(
        ok=not errors,
        version_id=version_id,
        topic_count=len(topic_guids),
        markup_count=markup_count,
        viewpoint_count=viewpoint_count,
        sha256=digest,
        errors=tuple(errors),
        xsd_status=xsd_status,
    )


__all__ = [
    "BcfStructuralVerification",
    "BcfTopicContract",
    "consume_bcf21_zip",
    "consume_bcf3_zip",
    "verify_bcf_zip_structure",
]
