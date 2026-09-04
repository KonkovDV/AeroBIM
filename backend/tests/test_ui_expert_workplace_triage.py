"""UI expert-workplace Red Team triage; customer_go stays false."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ui_expert_workplace_triage import (
    SCREEN_ROWS,
    TRIAGE_ROWS,
    ui_expert_workplace_triage_snapshot,
)


class UiExpertWorkplaceTriageTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_snapshot_stays_no_go(self) -> None:
        snap = ui_expert_workplace_triage_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["is_full_cycle_workplace"])
        self.assertFalse(snap["writes_summary_passed"])
        self.assertFalse(snap["native_rvt_in_ui"])
        self.assertFalse(snap["oidc_live"])
        self.assertFalse(snap["xlsx_export"])
        self.assertFalse(snap["cde_connector"])
        self.assertFalse(snap["stack_shipped"])
        self.assertFalse(snap["demo_seed_is_customer"])
        self.assertFalse(snap["demo_seed_writes_passed"])
        self.assertTrue(snap["jury_track_is_cli"])
        self.assertEqual(snap["artifact_type"], "ui_expert_workplace_red_team_triage")
        self.assertEqual(len(snap["screens"]), 8)
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 19)
        self.assertGreaterEqual(snap["hold_count"], 7)
        self.assertGreaterEqual(snap["accept_count"], 9)
        blob = json.dumps(snap)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)
        self.assertNotIn("DWG-ready", blob)
        self.assertNotIn("pack processed", blob)

    def test_ids_unique_and_markdown_lists_them(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        screen_ids = [row["id"] for row in SCREEN_ROWS]
        self.assertEqual(len(screen_ids), len(set(screen_ids)))
        md = (
            self._repo() / "docs" / "quality" / "UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md"
        ).read_text(encoding="utf-8")
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        for row in SCREEN_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn("customer_go", md)
        self.assertNotIn("DWG-ready", md)

    def test_frontend_screen_ssot_lists_ids(self) -> None:
        text = (self._repo() / "frontend" / "src" / "lib" / "tz-ui-screens.ts").read_text(
            encoding="utf-8"
        )
        for row in SCREEN_ROWS:
            self.assertIn(row["id"], text, msg=row["id"])
            self.assertIn(row["git"], text)

    def test_tier0_lists_ui_pin(self) -> None:
        text = (self._repo() / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md", text)
        self.assertIn("run_kt3_jury", text)
        self.assertIn("ИТ-ментора", text)

    def test_tz_matrix_web_ui_is_partial_not_done(self) -> None:
        text = (self._repo() / "docs" / "tz" / "TZ_COMPLIANCE_MATRIX_2026.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| Web UI | partial |", text)
        self.assertNotIn("| Web UI | done |", text)

    def test_hd13_fe01_frontend_source_scan_does_not_assign_summary_passed(self) -> None:
        """HD13-FE-01: walk production frontend/src; UI must not assign summary.passed."""
        root = self._repo() / "frontend" / "src"
        vitest_guard = root / "summary-passed-source-scan.test.ts"
        self.assertTrue(vitest_guard.is_file(), vitest_guard)
        self.assertIn("HD13-FE-01", vitest_guard.read_text(encoding="utf-8"))

        assign_field = re.compile(
            r"(?:^|[;\n{}()])\s*(?:[A-Za-z_$][\w$]*\.)*summary\s*\.\s*(?:passed|outcome)\s*=(?!=)"
        )
        assign_object = re.compile(r"(?:^|[;\n{}()])\s*(?:[A-Za-z_$][\w$]*\.)+summary\s*=(?!=)")
        literal_passed = re.compile(r"\bsummary\s*:\s*\{(?:[^{}]*)\bpassed\s*:\s*(?:true|false)")
        literal_outcome = re.compile(r"\bsummary\s*:\s*\{(?:[^{}]*)\boutcome\s*:\s*[\"'`]")
        bracket_assign = re.compile(r"summary\s*\[\s*[\"'](?:passed|outcome)[\"']\s*\]\s*=(?!=)")
        scanned = 0
        assigned: list[str] = []
        for path in root.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if path.name.endswith(".test.ts") or path.name.endswith(".test.tsx"):
                continue
            scanned += 1
            text = path.read_text(encoding="utf-8")
            rel = path.as_posix()
            if assign_field.search(text) or assign_object.search(text):
                assigned.append(rel)
                continue
            if literal_passed.search(text) or literal_outcome.search(text):
                assigned.append(rel)
                continue
            if bracket_assign.search(text):
                assigned.append(rel)
        self.assertGreaterEqual(scanned, 20)
        self.assertEqual(assigned, [])

    def test_seed_json_contract_omits_passed(self) -> None:
        demo = (
            self._repo()
            / "backend"
            / "src"
            / "aerobim"
            / "presentation"
            / "http"
            / "routes"
            / "demo.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"report_id": report.report_id', demo)
        self.assertNotIn('"passed": report.summary.passed', demo)
        api = (self._repo() / "frontend" / "src" / "lib" / "api.ts").read_text(encoding="utf-8")
        self.assertIn("issue_count: number", api)
        self.assertNotIn("passed: boolean", api.split("DemoSeedFixtureResponse")[1][:400])

    def test_frontend_intake_keys_match_domain(self) -> None:
        from aerobim.domain.intake_gate_keys import INTAKE_GATE_KEYS

        text = (self._repo() / "frontend" / "src" / "lib" / "intake-gates.ts").read_text(
            encoding="utf-8"
        )
        for key in INTAKE_GATE_KEYS:
            self.assertIn(f'"{key}"', text, msg=key)

    def test_frontend_css_does_not_load_google_fonts(self) -> None:
        css = (self._repo() / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")
        self.assertNotIn("fonts.googleapis.com", css)
        self.assertNotIn("fonts.gstatic.com", css)
        demo = (
            self._repo()
            / "backend"
            / "src"
            / "aerobim"
            / "presentation"
            / "http"
            / "routes"
            / "demo.py"
        ).read_text(encoding="utf-8")
        self.assertIn("include_in_schema=False", demo)


if __name__ == "__main__":
    unittest.main()
