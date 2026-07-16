"""Track A5 — demo path (upload → analyze → BCF) tests."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from aerobim.tools.run_demo_path import (
    _resolve_repo_file,
    _stage_into_storage,
    _validate_bcf_zip,
    normalize_bcf_version,
    pilot_moscow_pack_path,
    run_demo_path,
)


def _bcf_version_xml(version_id: str = "2.1") -> str:
    root = Element("Version", VersionId=version_id)
    SubElement(root, "DetailedVersion").text = version_id
    return tostring(root, encoding="unicode")


def _markup_xml() -> str:
    root = Element("Markup")
    topic = SubElement(root, "Topic", Guid="11111111-1111-1111-1111-111111111111")
    SubElement(topic, "Title").text = "Demo"
    return tostring(root, encoding="unicode")


def _build_bcf_zip(
    *,
    version_id: str = "2.1",
    include_version: bool = True,
    markup_name: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/markup.bcf",
    markup_body: str | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        if include_version:
            archive.writestr("bcf.version", _bcf_version_xml(version_id))
        if markup_name:
            archive.writestr(markup_name, markup_body if markup_body is not None else _markup_xml())
    return buffer.getvalue()


class DemoPathHelpersTests(unittest.TestCase):
    def test_normalize_bcf_version_allowlist(self) -> None:
        self.assertEqual(normalize_bcf_version("2.1"), "2.1")
        self.assertEqual(normalize_bcf_version("3"), "3.0")
        self.assertEqual(normalize_bcf_version("3.0"), "3.0")
        with self.assertRaises(ValueError):
            normalize_bcf_version("9.9")

    def test_stage_rejects_traversal_and_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jail = Path(tmp)
            source = jail / "ok.txt"
            source.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                _stage_into_storage(jail, source, "../escape.txt")
            with self.assertRaises(ValueError):
                _stage_into_storage(jail, source, "/etc/passwd")
            if Path("C:/").exists() or Path("C:\\").exists():
                with self.assertRaises(ValueError):
                    _stage_into_storage(jail, source, "C:/Windows/evil.txt")

    def test_resolve_repo_file_rejects_escape(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_repo_file("../outside.txt")

    def test_validate_bcf_zip_happy_path(self) -> None:
        meta = _validate_bcf_zip(_build_bcf_zip(), requested_version="2.1")
        self.assertEqual(meta["markup_topics"], 1)
        self.assertEqual(meta["version_observed"], "2.1")
        self.assertEqual(meta["check_level"], "structural_smoke")

    def test_validate_bcf_zip_rejects_version_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            _validate_bcf_zip(_build_bcf_zip(version_id="2.1"), requested_version="3.0")

    def test_validate_bcf_zip_rejects_suffix_trick(self) -> None:
        with self.assertRaises(ValueError):
            _validate_bcf_zip(
                _build_bcf_zip(markup_name="foomarkup.bcf"),
                requested_version="2.1",
            )

    def test_validate_bcf_zip_rejects_missing_topic(self) -> None:
        with self.assertRaises(ValueError):
            _validate_bcf_zip(
                _build_bcf_zip(markup_body="<Markup/>"),
                requested_version="2.1",
            )

    def test_validate_bcf_zip_rejects_empty_and_bad_zip(self) -> None:
        with self.assertRaises(ValueError):
            _validate_bcf_zip(b"", requested_version="2.1")
        with self.assertRaises(ValueError):
            _validate_bcf_zip(b"not-a-zip", requested_version="2.1")


class DemoPathIntegrationTests(unittest.TestCase):
    def test_run_demo_path_on_pilot_moscow_fixture(self) -> None:
        pack = pilot_moscow_pack_path()
        if not pack.is_file():
            self.skipTest("pilot moscow pack missing")
        result = run_demo_path(pack_path=pack, bcf_version="2.1")
        self.assertTrue(result["ok"])
        self.assertTrue(result["loop_ok"])
        self.assertIn("analyze_passed", result)
        self.assertEqual(result["track"], "A5")
        self.assertEqual(result["bcf_version_observed"], "2.1")
        self.assertEqual(
            result["pack_path"], "samples/benchmarks/project-package-pilot-moscow-v1.json"
        )
        self.assertEqual(result["storage_dir"], "<ephemeral>")
        self.assertTrue(result["sla_pass_fixture"])
        step_names = [step["step"] for step in result["steps"]]
        self.assertEqual(
            step_names,
            ["health", "upload_ifc", "analyze", "review_report", "export_html", "export_bcf"],
        )
        self.assertIn("multipart upload into storage jail", result["claim_boundary"]["proven"])
        self.assertIn("customer accuracy >90%", result["claim_boundary"]["not_proven"])
        bcf_step = result["steps"][-1]
        self.assertGreaterEqual(bcf_step["bcf"]["markup_topics"], 1)
        self.assertEqual(bcf_step["bcf"]["check_level"], "structural_smoke")

    def test_user_storage_dir_is_not_deleted(self) -> None:
        pack = pilot_moscow_pack_path()
        if not pack.is_file():
            self.skipTest("pilot moscow pack missing")
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp) / "jail"
            storage.mkdir()
            marker = storage / "keep-me.txt"
            marker.write_text("persist", encoding="utf-8")
            result = run_demo_path(pack_path=pack, storage_dir=storage)
            self.assertTrue(result["ok"])
            self.assertEqual(result["storage_dir"], "<user-provided>")
            self.assertTrue(storage.is_dir())
            self.assertTrue(marker.is_file())

    def test_cli_output_writes_json(self) -> None:
        pack = pilot_moscow_pack_path()
        if not pack.is_file():
            self.skipTest("pilot moscow pack missing")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo-path.json"
            from aerobim.tools import run_demo_path as mod

            argv = [
                "run_demo_path",
                "--pack",
                str(pack),
                "--output",
                str(out),
            ]
            with unittest.mock.patch("sys.argv", argv):
                mod.main()
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["storage_dir"], "<ephemeral>")


if __name__ == "__main__":
    unittest.main()
