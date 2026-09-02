"""UI expert-workplace Red Team triage stays NO_GO; shell is not a full cycle."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

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
        self.assertEqual(snap["checkpoint"], "NO_GO")
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
        self.assertIn("NO_GO", md)
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

    def test_frontend_does_not_assign_summary_passed(self) -> None:
        root = self._repo() / "frontend" / "src"
        assigned = []
        for path in root.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if path.name.endswith(".test.ts") or path.name.endswith(".test.tsx"):
                continue
            text = path.read_text(encoding="utf-8")
            display = (
                text.replace("<code>summary.passed=false</code>", "")
                .replace("summary.passed=false", "")
                .replace("summary.passed=true", "")
            )
            if "summary.passed =" in display or "summary.passed=" in display:
                assigned.append(path.as_posix())
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
