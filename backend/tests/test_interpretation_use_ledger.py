"""Kane IUA ledger: no row licenses customer precision or RT close."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.interpretation_use import (
    AUDITED_HEAD,
    CHECKPOINT,
    FORBIDDEN_LICENSED_USES,
    LEDGER,
    ledger_payload,
    validate_ledger,
)
from aerobim.tools.export_interpretation_use_ledger import main as export_main


class InterpretationUseLedgerTests(unittest.TestCase):
    def test_ledger_is_internally_consistent(self) -> None:
        validate_ledger()
        self.assertGreaterEqual(len(LEDGER), 18)
        sources = {row.source for row in LEDGER}
        self.assertTrue({"samolet", "tracker", "techlab", "mik", "industry"}.issubset(sources))
        self.assertTrue(all(row.licensed_use not in FORBIDDEN_LICENSED_USES for row in LEDGER))
        self.assertTrue(all(not row.closes_rt001 for row in LEDGER))

    def test_payload_stays_no_go(self) -> None:
        payload = ledger_payload(generated_at="2026-08-16T00:00:00+00:00")
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        self.assertEqual(payload["audited_head"], AUDITED_HEAD)
        self.assertFalse(payload["closes_rt001"])
        self.assertEqual(payload["row_count"], len(payload["rows"]))
        ids = {row["row_id"] for row in payload["rows"]}
        self.assertIn("TRK-03", ids)
        self.assertIn("IND-01", ids)
        self.assertIn("IND-06", ids)
        self.assertIn("IND-10", ids)
        self.assertIn("IND-14", ids)
        self.assertIn("IND-15", ids)
        self.assertIn("IND-16", ids)
        self.assertIn("IND-17", ids)
        self.assertIn("IND-18", ids)
        self.assertIn("IND-19", ids)
        self.assertIn("IND-20", ids)
        self.assertIn("IND-21", ids)
        self.assertIn("IND-22", ids)
        self.assertIn("IND-23", ids)
        self.assertIn("MIK-03", ids)
        self.assertIn("MIK-04", ids)
        self.assertIn("MIK-05", ids)
        self.assertIn("MIK-06", ids)
        self.assertIn("MIK-07", ids)
        self.assertIn("MIK-08", ids)
        self.assertIn("MIK-09", ids)
        self.assertIn("MIK-10", ids)
        self.assertIn("TL-04", ids)
        self.assertIn("TL-10", ids)
        self.assertIn("TL-11", ids)
        self.assertIn("TL-12", ids)
        self.assertIn("TL-13", ids)
        self.assertIn("TL-14", ids)
        self.assertIn("TL-15", ids)
        self.assertIn("TL-16", ids)
        self.assertIn("MIK-11", ids)
        self.assertIn("MIK-12", ids)
        self.assertIn("IND-24", ids)
        self.assertIn("IND-25", ids)
        self.assertIn("IND-26", ids)
        self.assertIn("SAM-11", ids)
        self.assertIn("IND-27", ids)
        self.assertIn("IND-28", ids)
        self.assertIn("SAM-12", ids)
        self.assertIn("IND-29", ids)
        self.assertIn("PLAN-06", ids)
        self.assertIn("TL-17", ids)
        self.assertIn("SAM-10", ids)
        self.assertIn("PLAN-00", ids)
        self.assertIn("PLAN-05", ids)
        self.assertIn("SIG-01", ids)
        self.assertIn("SIG-02", ids)
        trk01 = next(row for row in payload["rows"] if row["row_id"] == "TRK-01")
        self.assertIn("run_kt3_jury", trk01["licensed_inference"])
        self.assertIn("KT3_TRACKER_DMITRY_2026_08.md", trk01["evidence"])
        self.assertEqual(payload["schema_version"], "1.2.1")
        self.assertGreaterEqual(payload["row_count"], 22)
        self.assertEqual(len(ids), payload["row_count"])

    def test_evidence_markdown_links_files_and_keeps_cli_as_code(self) -> None:
        from aerobim.domain.interpretation_use import (
            _evidence_href,
            _evidence_label,
            render_markdown,
        )

        self.assertEqual(
            _evidence_href("docs/architecture/ADR-001-verdict-ownership-2026.md"),
            "../architecture/ADR-001-verdict-ownership-2026.md",
        )
        self.assertEqual(
            _evidence_href("docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md"),
            "INTERPRETATION_USE_LEDGER_2026_08.md",
        )
        self.assertEqual(
            _evidence_href("samples/ids-xsd/ids.xsd"),
            "../../samples/ids-xsd/ids.xsd",
        )
        self.assertEqual(
            _evidence_label("docs/architecture/ADR-001-verdict-ownership-2026.md"),
            "ADR-001-verdict-ownership-2026.md",
        )
        markdown = render_markdown(ledger_payload(generated_at="2026-08-17T00:00:00+00:00"))
        self.assertIn(
            "[ADR-001-verdict-ownership-2026.md](../architecture/ADR-001-verdict-ownership-2026.md)",
            markdown,
        )
        self.assertIn("`python -m aerobim.tools.run_demo_ifc_acceptance_gate`", markdown)
        self.assertNotIn("](python -m ", markdown)

    def test_export_writes_docs_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ledger.json"
            code = export_main(["--output", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_type"], "aerobim_interpretation_use_ledger")
            self.assertEqual(payload["checkpoint"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
