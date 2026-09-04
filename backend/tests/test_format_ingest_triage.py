"""Format-ingest Red Team triage stays NO_GO; natives stay fail-closed."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.format_ingest_triage import (
    KT3_RECOMMENDED,
    STRATEGY_CLASSES,
    TRIAGE_ROWS,
    format_ingest_triage_snapshot,
)


class FormatIngestTriageTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_snapshot_stays_no_go(self) -> None:
        snap = format_ingest_triage_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["is_dwg_ready"])
        self.assertFalse(snap["is_native_rvt"])
        self.assertFalse(snap["is_native_nwd"])
        self.assertFalse(snap["is_lira_solver"])
        self.assertFalse(snap["navisworks_stock_ifc_export"])
        self.assertEqual(snap["artifact_type"], "format_ingest_red_team_triage")
        self.assertEqual(snap["kt3_recommended"]["dwg"], "fail_closed_pdf_same_mark")
        self.assertEqual(len(STRATEGY_CLASSES), 7)
        self.assertEqual(KT3_RECOMMENDED["lir"], "compare_notes_not_parse")
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 12)
        self.assertGreaterEqual(snap["hold_count"], 3)
        self.assertGreaterEqual(snap["accept_count"], 4)
        blob = json.dumps(snap)
        self.assertNotIn("ГиБ", blob)
        self.assertNotIn("GiB", blob)
        self.assertNotIn("DWG-ready", blob)

    def test_ids_unique_and_verdicts_known(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"KILL", "HOLD", "ACCEPT"}
        for row in TRIAGE_ROWS:
            self.assertIn(row["verdict"], allowed)
            self.assertTrue(row["brake"])

    def test_required_ids(self) -> None:
        ids = {row["id"] for row in TRIAGE_ROWS}
        for row_id in (
            "RT-FMT-DWG-PRODUCT",
            "RT-FMT-PARSE-NWD",
            "RT-FMT-NAVIS-IFC",
            "RT-FMT-PARSE-LIR",
            "RT-FMT-SUSTAINING-RVT",
            "RT-FMT-LIBREDWG",
            "RT-FMT-EZDXF-DWG",
            "RT-FMT-OCR-DONE",
            "RT-FMT-BENCH-OURS",
            "RT-FMT-ODA-PRODUCT",
            "RT-FMT-ADSK-BUY",
            "RT-FMT-RAISE-SPF",
            "RT-FMT-ODA-TRIAL",
            "RT-FMT-SDK-SIGN",
            "RT-FMT-GPL-PROC",
            "RT-FMT-EXCHANGE",
            "RT-FMT-FAIL-CLOSED",
            "RT-FMT-CC-NOTE",
            "RT-FMT-SEVEN",
        ):
            self.assertIn(row_id, ids)

    def test_markdown_lists_every_triage_id(self) -> None:
        md = (self._repo() / "docs" / "quality" / "FORMAT_INGEST_TRIAGE_2026_09.md").read_text(
            encoding="utf-8"
        )
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", md, msg=row["id"])
        self.assertIn("customer_go", md)
        self.assertNotIn("DWG-ready", md)
        self.assertNotIn("81 ГиБ", md)
        self.assertNotIn("pack_hash", md)
