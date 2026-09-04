"""Ishigaki-IDS-Bench gold IDS audit: SKIPPED without files; processability only."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.tools.run_ishigaki_ids_bench_smoke import audit_gold_ids, skipped_payload

_TINY_IDS = """<?xml version="1.0" encoding="utf-8"?>
<ids xmlns:xs="http://www.w3.org/2001/XMLSchema"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://standards.buildingsmart.org/IDS http://standards.buildingsmart.org/IDS/1.0/ids.xsd"
     xmlns="http://standards.buildingsmart.org/IDS">
  <info>
    <title>Ishigaki fixture</title>
  </info>
  <specifications>
    <specification name="Walls" ifcVersion="IFC4">
      <applicability minOccurs="0" maxOccurs="unbounded">
        <entity>
          <name>
            <simpleValue>IFCWALL</simpleValue>
          </name>
        </entity>
      </applicability>
      <requirements>
        <attribute>
          <name>
            <simpleValue>Name</simpleValue>
          </name>
        </attribute>
      </requirements>
    </specification>
  </specifications>
</ids>
"""


class IshigakiIdsBenchSmokeTests(unittest.TestCase):
    def test_skipped_payload_is_not_a_score(self) -> None:
        payload = skipped_payload(reason="missing", dataset_root=".local/ishigaki-ids-bench")
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertEqual(payload["claim_level"], "open_bench_only")
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["citation"]["real_ifc"])
        self.assertEqual(payload["summary"]["audited"], 0)

    def test_empty_dir_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty = root / "empty"
            empty.mkdir()
            payload = audit_gold_ids(empty, repo=root)
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertIn("test.jsonl", payload["reason"])

    def test_audits_local_gold_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "ishigaki"
            pack.mkdir()
            (pack / "gold-01.ids").write_text(_TINY_IDS, encoding="utf-8")
            payload = audit_gold_ids(pack, repo=root, auditor=XmlIdsDocumentAuditor())
        self.assertEqual(payload["status"], "EXECUTED")
        self.assertEqual(payload["summary"]["ids_files"], 1)
        self.assertEqual(payload["summary"]["audited"], 1)
        self.assertFalse(payload["citation"]["real_ifc"])
        raw = json.dumps(payload)
        self.assertIn("open_bench_only", raw)

    def test_extracts_gold_ids_from_hf_jsonl(self) -> None:
        from aerobim.tools.run_ishigaki_ids_bench_smoke import audit_gold_ids

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack = root / "ishigaki"
            (pack / "data").mkdir(parents=True)
            row = {
                "id": "row-0001",
                "messages": [
                    {"role": "user", "content": "filename: row-0001.ids"},
                    {"role": "assistant", "content": _TINY_IDS},
                ],
                "language": "en",
            }
            (pack / "data" / "test.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
            payload = audit_gold_ids(pack, repo=root, auditor=XmlIdsDocumentAuditor())
        self.assertEqual(payload["status"], "EXECUTED")
        self.assertEqual(payload["source"]["kind"], "hf_test_jsonl")
        self.assertEqual(payload["summary"]["audited"], 1)
        self.assertFalse(payload["citation"]["real_ifc"])
        self.assertEqual(payload["checkpoint"], CHECKPOINT)


if __name__ == "__main__":
    unittest.main()
