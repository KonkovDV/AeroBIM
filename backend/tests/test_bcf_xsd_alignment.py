"""BCF XSD alignment + triage handoff (Wave C, Jul 2026).

Anchors: official buildingSMART BCF-XML schemas (release_2_1 / release_3_0
markup.xsd); BIMcollab accepts BCF 3.0 import since 2026-02-20, so structural
XSD fidelity is consumer-visible. Claim boundary: structural alignment only —
no CDE import claim (RT-008 T2 stays customer-gated).
"""

from __future__ import annotations

import io
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

from aerobim.core.security.xml_limits import safe_fromstring
from aerobim.domain.models import (
    ClashResult,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.bcf3_exporter import export_bcf3
from aerobim.infrastructure.adapters.bcf_report_exporter import export_bcf

# markup.xsd Topic child sequences (subset we emit), release_2_1 and release_3_0.
_TOPIC_ORDER_21 = [
    "ReferenceLink",
    "Title",
    "Priority",
    "Index",
    "Labels",
    "CreationDate",
    "CreationAuthor",
    "Description",
]
_TOPIC_ORDER_30 = [
    "ReferenceLinks",
    "Title",
    "Priority",
    "Index",
    "Labels",
    "CreationDate",
    "CreationAuthor",
    "ModifiedDate",
    "ModifiedAuthor",
    "Description",
    "Comments",
    "Viewpoints",
]


def _clash(a: str, b: str, clash_type: str, distance: float) -> ClashResult:
    return ClashResult(
        element_a_guid=a,
        element_b_guid=b,
        clash_type=clash_type,
        distance=distance,
        description=f"{a} vs {b}",
    )


def _report(clashes: tuple[ClashResult, ...]) -> ValidationReport:
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-bcf-xsd",
        ifc_path=Path("test.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(),
        summary=ValidationSummary(0, 0, 0, 0, True),
        clash_results=clashes,
    )


def _markup_roots(archive: bytes) -> list[ET.Element]:
    roots: list[ET.Element] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        for name in sorted(n for n in zf.namelist() if n.endswith("/markup.bcf")):
            roots.append(safe_fromstring(zf.read(name)))
    return roots


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _assert_subsequence(test: unittest.TestCase, children: list[str], order: list[str]) -> None:
    """Children must appear in XSD-relative order (missing optionals allowed)."""
    positions = [order.index(tag) for tag in children if tag in order]
    test.assertEqual(positions, sorted(positions), msg=f"children={children}")


class Bcf21XsdOrderTests(unittest.TestCase):
    def test_topic_children_follow_markup_xsd_sequence(self) -> None:
        archive = export_bcf(_report((_clash("a", "b", "hard", 0.06),)))
        for root in _markup_roots(archive):
            topic = next(el for el in root.iter() if _local(el.tag) == "Topic")
            children = [_local(child.tag) for child in topic]
            _assert_subsequence(self, children, _TOPIC_ORDER_21)

    def test_clash_topic_carries_priority_and_index_from_triage(self) -> None:
        archive = export_bcf(_report((_clash("a", "b", "hard", 0.06),)))
        topic = next(el for el in _markup_roots(archive)[0].iter() if _local(el.tag) == "Topic")
        by_tag = {_local(child.tag): (child.text or "") for child in topic}
        self.assertEqual(by_tag.get("Priority"), "Critical")
        self.assertEqual(by_tag.get("Index"), "1")
        labels = [(child.text or "") for child in topic if _local(child.tag) == "Labels"]
        self.assertIn("triage:band=critical", labels)

    def test_clash_topic_guid_stable_across_input_order(self) -> None:
        clashes = (
            _clash("w1", "p1", "hard", 0.06),
            _clash("w2", "p2", "clearance", 0.001),
        )
        report_a = _report(clashes)
        report_b = ValidationReport(
            **{**report_a.__dict__, "clash_results": tuple(reversed(clashes))}
        )

        def _topic_guids(archive: bytes) -> set[str]:
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                return {n.split("/", 1)[0] for n in zf.namelist() if n.endswith("/markup.bcf")}

        self.assertEqual(_topic_guids(export_bcf(report_a)), _topic_guids(export_bcf(report_b)))

    def test_symmetric_duplicate_clashes_merge_into_one_topic(self) -> None:
        archive = export_bcf(
            _report(
                (
                    _clash("duct", "pipe", "hard", 0.010),
                    _clash("pipe", "duct", "hard", 0.055),
                )
            )
        )
        self.assertEqual(len(_markup_roots(archive)), 1)


class Bcf30XsdOrderTests(unittest.TestCase):
    def test_topic_children_follow_markup_xsd_sequence(self) -> None:
        archive = export_bcf3(_report((_clash("a", "b", "hard", 0.06),)))
        for root in _markup_roots(archive):
            topic = root.find("Topic")
            assert topic is not None
            children = [_local(child.tag) for child in topic]
            _assert_subsequence(self, children, _TOPIC_ORDER_30)

    def test_reference_links_and_labels_are_wrapped(self) -> None:
        archive = export_bcf3(_report((_clash("a", "b", "hard", 0.06),)))
        topic = _markup_roots(archive)[0].find("Topic")
        assert topic is not None
        reference_links = topic.find("ReferenceLinks")
        self.assertIsNotNone(reference_links)
        assert reference_links is not None
        self.assertGreaterEqual(len(reference_links.findall("ReferenceLink")), 1)
        labels = topic.find("Labels")
        self.assertIsNotNone(labels)
        assert labels is not None
        label_texts = [(el.text or "") for el in labels.findall("Label")]
        self.assertIn("triage:band=critical", label_texts)

    def test_priority_from_triage_band(self) -> None:
        archive = export_bcf3(_report((_clash("a", "b", "clearance", 0.030),)))
        topic = _markup_roots(archive)[0].find("Topic")
        assert topic is not None
        priority = topic.find("Priority")
        self.assertIsNotNone(priority)
        assert priority is not None
        self.assertEqual(priority.text, "Minor")

    def test_header_wraps_files_file(self) -> None:
        archive = export_bcf3(_report((_clash("a", "b", "hard", 0.06),)))
        root = _markup_roots(archive)[0]
        self.assertIsNotNone(root.find("Header/Files/File"))

    def test_markup_has_only_header_and_topic_children(self) -> None:
        # markup.xsd (release_3_0): Markup contains Header? and Topic only.
        archive = export_bcf3(_report((_clash("a", "b", "hard", 0.06),)))
        root = _markup_roots(archive)[0]
        self.assertEqual([_local(c.tag) for c in root], ["Header", "Topic"])


class Bcf30ExtensionsTests(unittest.TestCase):
    """Root extensions.xml (extensions.xsd) — predefined vocabularies for consumers."""

    def test_extensions_xml_present_and_declares_used_vocabularies(self) -> None:
        archive = export_bcf3(_report((_clash("a", "b", "hard", 0.06),)))
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            self.assertIn("extensions.xml", zf.namelist())
            extensions = safe_fromstring(zf.read("extensions.xml"))
        priorities = [(el.text or "") for el in extensions.findall("Priorities/Priority")]
        self.assertIn("Critical", priorities)
        topic_types = [(el.text or "") for el in extensions.findall("TopicTypes/TopicType")]
        self.assertIn("Clash", topic_types)
        statuses = [(el.text or "") for el in extensions.findall("TopicStatuses/TopicStatus")]
        self.assertIn("Open", statuses)
        labels = [(el.text or "") for el in extensions.findall("TopicLabels/TopicLabel")]
        self.assertIn("triage:band=critical", labels)

    def test_empty_report_has_no_extensions_xml(self) -> None:
        archive = export_bcf3(_report(()))
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            self.assertNotIn("extensions.xml", zf.namelist())

    def test_markup_vocabulary_is_subset_of_extensions(self) -> None:
        """Implementation agreement: topic values resolve against extensions lists."""
        archive = export_bcf3(
            _report(
                (
                    _clash("a", "b", "hard", 0.06),
                    _clash("c", "d", "clearance", 0.030),
                )
            )
        )
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            extensions = safe_fromstring(zf.read("extensions.xml"))
            declared_priorities = {
                (el.text or "") for el in extensions.findall("Priorities/Priority")
            }
            declared_types = {(el.text or "") for el in extensions.findall("TopicTypes/TopicType")}
            declared_labels = {
                (el.text or "") for el in extensions.findall("TopicLabels/TopicLabel")
            }
            for name in (n for n in zf.namelist() if n.endswith("/markup.bcf")):
                topic = safe_fromstring(zf.read(name)).find("Topic")
                assert topic is not None
                priority = topic.find("Priority")
                if priority is not None:
                    self.assertIn(priority.text, declared_priorities)
                self.assertIn(topic.get("TopicType"), declared_types)
                labels_node = topic.find("Labels")
                if labels_node is not None:
                    for label in labels_node.findall("Label"):
                        self.assertIn(label.text, declared_labels)

    def test_extensions_xml_is_deterministic(self) -> None:
        clashes = (
            _clash("a", "b", "hard", 0.06),
            _clash("c", "d", "clearance", 0.030),
        )
        report = _report(clashes)

        def _extensions_bytes(archive: bytes) -> bytes:
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                return zf.read("extensions.xml")

        shuffled = ValidationReport(
            **{**report.__dict__, "clash_results": tuple(reversed(clashes))}
        )
        self.assertEqual(
            _extensions_bytes(export_bcf3(report)),
            _extensions_bytes(export_bcf3(shuffled)),
        )


class OfficialXsdValidationTests(unittest.TestCase):
    """End-to-end validation against vendored official buildingSMART XSDs."""

    def setUp(self) -> None:
        try:
            import xmlschema  # noqa: F401
        except ImportError:
            self.skipTest("xmlschema not installed")

    @staticmethod
    def _valid_clash() -> ClashResult:
        # Valid 22-char IfcGuids — required by visinfo.xsd Component/IfcGuid.
        return ClashResult(
            element_a_guid="3ZAR7ASd14MuxcHc7_fqIb",
            element_b_guid="0aKrY0eXn00Qu9HBZ7Ao4t",
            clash_type="hard",
            distance=0.06,
            description="duct vs pipe",
        )

    def test_bcf21_export_passes_official_xsd(self) -> None:
        from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure

        result = verify_bcf_zip_structure(export_bcf(_report((self._valid_clash(),))))
        self.assertEqual(result.xsd_status, "passed", msg=result.errors)
        self.assertTrue(result.ok, msg=result.errors)

    def test_bcf30_export_passes_official_xsd(self) -> None:
        from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure

        result = verify_bcf_zip_structure(export_bcf3(_report((self._valid_clash(),))))
        self.assertEqual(result.xsd_status, "passed", msg=result.errors)
        self.assertTrue(result.ok, msg=result.errors)

    def test_tampered_extensions_fails_xsd(self) -> None:
        from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure

        archive = export_bcf3(_report((self._valid_clash(),)))
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            entries = {name: zf.read(name) for name in zf.namelist()}
        # Unknown child violates extensions.xsd sequence.
        entries["extensions.xml"] = (
            entries["extensions.xml"]
            .decode("utf-8")
            .replace("</Extensions>", "<Bogus/></Extensions>")
            .encode("utf-8")
        )
        rebuilt = io.BytesIO()
        with zipfile.ZipFile(rebuilt, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, payload in entries.items():
                zf.writestr(name, payload)
        result = verify_bcf_zip_structure(rebuilt.getvalue())
        self.assertEqual(result.xsd_status, "failed")
        self.assertTrue(any("extensions.xml" in error for error in result.errors))

    def test_tampered_markup_fails_xsd(self) -> None:
        from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure

        archive = export_bcf(_report((self._valid_clash(),)))
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            entries = {name: zf.read(name) for name in zf.namelist()}
        markup_name = next(n for n in entries if n.endswith("/markup.bcf"))
        # Move Title after CreationDate — violates the markup.xsd Topic sequence.
        broken = (
            entries[markup_name]
            .decode("utf-8")
            .replace("<Title>", "<CreationDate>2026-07-25T00:00:00+00:00</CreationDate><Title>", 1)
        )
        entries[markup_name] = broken.encode("utf-8")
        rebuilt = io.BytesIO()
        with zipfile.ZipFile(rebuilt, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, payload in entries.items():
                zf.writestr(name, payload)
        result = verify_bcf_zip_structure(rebuilt.getvalue())
        self.assertEqual(result.xsd_status, "failed")
        self.assertFalse(result.ok)
        self.assertTrue(any("XSD invalid" in error for error in result.errors))

    def test_invalid_ifcguid_fails_xsd(self) -> None:
        from aerobim.infrastructure.adapters.bcf_consumers import verify_bcf_zip_structure

        bad = ClashResult(
            element_a_guid="clash-a",
            element_b_guid="clash-b",
            clash_type="hard",
            distance=0.06,
            description="bad guids",
        )
        result = verify_bcf_zip_structure(export_bcf(_report((bad,))))
        self.assertEqual(result.xsd_status, "failed")


if __name__ == "__main__":
    unittest.main()
