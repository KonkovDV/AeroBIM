"""Audit vendored jurisdiction IDS files with XmlIdsDocumentAuditor.

Not the official buildingSMART IDS-Audit-tool binary. Not customer_pack_hash.
Does not close RT-002.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor

REPO = Path(__file__).resolve().parents[2]

_JURISDICTION_IDS = (
    REPO
    / "samples"
    / "ids"
    / "moexp"
    / "pack"
    / "oks"
    / "IDS_v1.1_Проверка_КСИ_элементов_ЦИМ_МОГЭ_АР_v3.2.ids",
    REPO / "samples" / "ids" / "moscow-agr" / "pack" / "АГР_ЦИМ БиО v8.ids",
    REPO
    / "samples"
    / "ids"
    / "spbexp"
    / "pack"
    / "rii"
    / "ЦГЭ.ЦИМ.РИИ_ИГДИ_Рельеф_1.1.0_(IDS_1.0).ids",
)


class JurisdictionIdsAuditTests(unittest.TestCase):
    def test_auditor_runs_on_official_ids_without_closing_rt002(self) -> None:
        auditor = XmlIdsDocumentAuditor()
        missing = [path for path in _JURISDICTION_IDS if not path.is_file()]
        if missing:
            self.skipTest(f"jurisdiction IDS missing: {missing[0].name}")
        for path in _JURISDICTION_IDS:
            issues = auditor.audit(path)
            self.assertIsInstance(issues, list, msg=path.name)
            # Official files may carry schema/facet gaps; record, do not rewrite them.
            for issue in issues:
                self.assertTrue(issue.rule_id)
                self.assertNotIn("closes_rt002=true", issue.message.casefold())
        evidence = REPO / "docs" / "evidence" / "ids-audit-2026-08.json"
        if evidence.is_file():
            payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertFalse(payload["closes_rt002"])
            self.assertIsNone(payload["customer_pack_hash"])
            self.assertTrue(payload["not_buildingsmart_ids_audit_tool_binary"])


if __name__ == "__main__":
    unittest.main()
