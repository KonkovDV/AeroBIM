"""PNST 909 22-scenario runtime CLI: pairing, path jail, no silent pass."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.core.security.path_jail import PathJailError
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.run_pnst909_22_scenario_runtime import (
    default_pairing_path,
    load_pairing,
    main,
    repo_root,
    run_scenarios,
    skipped_pack_payload,
)

_TINY_IFC = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition[DesignTransferView]'),'2;1');
FILE_NAME('pnst-fixture.ifc','2026-08-15T00:00:00',(''),(''),'IfcOpenShell','IfcOpenShell','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('3JnsKeWMP9xBNxnCYr$wB9',$,'PNST fixture',$,$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;
"""

_TINY_IDS = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns="http://standards.buildingsmart.org/IDS">
  <info><title>PNST fixture</title></info>
  <specifications>
    <specification name="Walls" ifcVersion="IFC4">
      <applicability maxOccurs="unbounded">
        <entity><name><simpleValue>IFCWALL</simpleValue></name></entity>
      </applicability>
      <requirements>
        <attribute><name><simpleValue>Name</simpleValue></name></attribute>
      </requirements>
    </specification>
  </specifications>
</ids>
"""


class _CleanValidator:
    def validate(self, ids_path: Path, ifc_path: Path) -> list[object]:
        assert ids_path.is_file()
        assert ifc_path.is_file()
        return []


class _FindingValidator:
    def validate(self, ids_path: Path, ifc_path: Path) -> list[object]:
        assert ids_path.is_file()
        assert ifc_path.is_file()
        return [object(), object()]


class _BoomValidator:
    def validate(self, ids_path: Path, ifc_path: Path) -> list[object]:
        raise RuntimeError(f"boom {ids_path.name}")


def _write_pack(tmp: Path) -> Path:
    pack = tmp / "pack"
    (pack / "IDS" / "C1").mkdir(parents=True)
    (pack / "IFC" / "C1").mkdir(parents=True)
    (pack / "IDS" / "C1" / "s1.ids").write_text(_TINY_IDS, encoding="utf-8")
    (pack / "IFC" / "C1" / "m1.ifc").write_text(_TINY_IFC, encoding="utf-8")
    return pack


def _pairing_three() -> list[dict[str, str | int | None]]:
    return [
        {"scenario": 1, "ids_path": "IDS/C1/s1.ids", "ifc_path": "IFC/C1/m1.ifc"},
        {"scenario": 2, "ids_path": None, "ifc_path": "IFC/C1/m1.ifc"},
        {"scenario": 3, "ids_path": "IDS/missing.ids", "ifc_path": "IFC/C1/m1.ifc"},
    ]


class Pnst909RuntimeTests(unittest.TestCase):
    def test_repo_pairing_covers_22_and_out_of_pack(self) -> None:
        path = default_pairing_path(repo_root())
        rows = load_pairing(path)
        self.assertEqual(len(rows), 22)
        missing = {row["scenario"] for row in rows if row["ids_path"] is None}
        self.assertEqual(missing, {3, 18, 21, 22})

    def test_load_pairing_rejects_short_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pairing.json"
            path.write_text(
                json.dumps({"scenarios": [{"scenario": 1, "ids_path": None, "ifc_path": "a.ifc"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_pairing(path)

    def test_run_clean_and_no_ids_not_silent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = _write_pack(root)
            payload = run_scenarios(
                pack_root=pack,
                pairing=_pairing_three(),
                validator=_CleanValidator(),
                repo=root,
                pairing_path="pairing.json",
            )
        by_n = {row["scenario"]: row for row in payload["scenarios"]}
        self.assertEqual(by_n[1]["runtime_status"], "EXECUTED")
        self.assertEqual(by_n[1]["issue_count"], 0)
        self.assertEqual(by_n[1]["coverage_class"], "runtime_clean")
        self.assertEqual(by_n[2]["runtime_status"], "NO_IDS_IN_PACK")
        self.assertIsNone(by_n[2]["issue_count"])
        self.assertEqual(by_n[3]["runtime_status"], "NO_IDS_IN_PACK")
        self.assertEqual(payload["summary"]["executed"], 1)
        self.assertFalse(payload["closes_rt001"])
        self.assertEqual(payload["checkpoint"], CHECKPOINT)

    def test_findings_are_runtime_findings_not_precision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = _write_pack(root)
            payload = run_scenarios(
                pack_root=pack,
                pairing=_pairing_three()[:1],
                validator=_FindingValidator(),
                repo=root,
                pairing_path="pairing.json",
            )
        row = payload["scenarios"][0]
        self.assertEqual(row["runtime_status"], "EXECUTED")
        self.assertEqual(row["coverage_class"], "runtime_findings")
        self.assertEqual(row["issue_count"], 2)

    def test_validator_error_is_not_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = _write_pack(root)
            payload = run_scenarios(
                pack_root=pack,
                pairing=_pairing_three()[:1],
                validator=_BoomValidator(),
                repo=root,
                pairing_path="pairing.json",
            )
        row = payload["scenarios"][0]
        self.assertEqual(row["runtime_status"], "ERROR")
        self.assertIn("boom", row["error"] or "")

    def test_path_jail_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = _write_pack(root)
            pairing = [
                {
                    "scenario": 1,
                    "ids_path": "../escape.ids",
                    "ifc_path": "IFC/C1/m1.ifc",
                }
            ]
            payload = run_scenarios(
                pack_root=pack,
                pairing=pairing,
                validator=_CleanValidator(),
                repo=root,
                pairing_path="pairing.json",
            )
        row = payload["scenarios"][0]
        self.assertEqual(row["runtime_status"], "PATH_REJECTED")
        self.assertTrue(row["error"])
        with self.assertRaises(PathJailError):
            from aerobim.core.security.path_jail import resolve_storage_path

            resolve_storage_path("../escape.ids", base=pack)

    def test_skipped_pack_does_not_invent_18_of_22(self) -> None:
        payload = skipped_pack_payload(reason="missing pack", pairing_path="pairing.json")
        self.assertEqual(payload["status"], "SKIPPED_PACK_ABSENT")
        self.assertEqual(payload["summary"]["executed"], 0)
        self.assertEqual(payload["scenarios"], [])
        self.assertIn("Do not invent", payload["note"])

    def test_main_skips_truncated_header_sample_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp) / "pack"
            (pack / "IFC").mkdir(parents=True)
            (pack / "IFC" / "header-only.ifc").write_text(_TINY_IFC, encoding="utf-8")
            out = Path(tmp) / "out.json"
            pairing = Path(tmp) / "pairing.json"
            pairing.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {
                                "scenario": n,
                                "ids_path": None if n in {3, 18, 21, 22} else f"IDS/C{n}/s.ids",
                                "ifc_path": f"IFC/C{n}/x.ifc",
                            }
                            for n in range(1, 23)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            code = main(
                [
                    "--pack-root",
                    str(pack),
                    "--pairing",
                    str(pairing),
                    "--output",
                    str(out),
                    "--write-docs-evidence",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "SKIPPED_PACK_INCOMPLETE")
            self.assertEqual(payload["summary"]["executed"], 0)

    def test_main_skips_when_pack_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            pairing = Path(tmp) / "pairing.json"
            pairing.write_text(
                json.dumps(
                    {
                        "scenarios": [
                            {"scenario": n, "ids_path": None, "ifc_path": f"IFC/C{n}/x.ifc"}
                            for n in range(1, 23)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            code = main(
                [
                    "--pack-root",
                    str(Path(tmp) / "no-such-pack"),
                    "--pairing",
                    str(pairing),
                    "--output",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "SKIPPED_PACK_ABSENT")


if __name__ == "__main__":
    unittest.main()
