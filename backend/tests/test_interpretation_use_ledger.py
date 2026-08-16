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
        self.assertGreaterEqual(payload["row_count"], 22)
        self.assertEqual(len(ids), payload["row_count"])

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
