"""Demo-day auditor pack pins A–F to git evidence; no customer fabrication."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.demo_day_auditor_pack import (
    CONTRADICTIONS,
    CUSTOMER_LETTER,
    DANGEROUS_QUESTIONS,
    DEMO_20S,
    E1_TEXT,
    E2_TEXT,
    E3_TEXT,
    E4_TEXT,
    E5_TEXT,
    FACT_ROWS,
    NON_CLAIM_COUNT,
    SLIDE_LINE_MAX,
    STATUSES,
    demo_day_auditor_snapshot,
    fact_by_id,
    render_auditor_document,
    render_fact_table,
)
from aerobim.domain.finding_volume import REPORT_PHRASE
from aerobim.domain.jury_pack_triage import JURY_FINGERPRINT_TOKENS, JURY_SURFACES
from aerobim.domain.unpack_census import PUBLIC_UNPACK_CENSUS

_REPO = Path(__file__).resolve().parents[2]
_AUDITOR_MD = _REPO / "docs" / "quality" / "DEMO_DAY_AUDITOR_PACK_2026_09.md"


def _load_json(rel: str) -> object:
    raw = (_REPO / rel).read_text(encoding="utf-8")
    if raw.lstrip().startswith("<!--"):
        raw = raw.split("-->", 1)[1]
    return json.loads(raw)


def _non_claim_count(text: str) -> int:
    start = text.index("## Non-claims")
    end = text.index("## Reproducibility")
    nums = [int(n) for n in re.findall(r"^(\d+)\. ", text[start:end], re.M)]
    return max(nums) if nums else 0


class DemoDayAuditorPackTests(unittest.TestCase):
    def test_snapshot_stays_measurement_only(self) -> None:
        snap = demo_day_auditor_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertFalse(snap["customer_go"])
        self.assertFalse(snap["is_pack_processed"])
        self.assertFalse(snap["is_accuracy"])
        self.assertFalse(snap["precision_claim_publishable"])
        self.assertEqual(snap["publishable_finding_count"], 0)
        self.assertFalse(snap["trl_5_claimed"])
        self.assertEqual(snap["trl_self_assess"], 4)
        self.assertEqual(snap["recommended_n"], 111)
        self.assertEqual(snap["non_claim_count"], NON_CLAIM_COUNT)
        self.assertEqual(snap["dangerous_question_count"], 10)
        self.assertEqual(snap["fact_count"], len(FACT_ROWS))
        blob = json.dumps(snap, ensure_ascii=False)
        self.assertNotIn("pack_hash", blob)
        for token in ("2552", "6408", "10599"):
            self.assertNotIn(token, blob)

    def test_ids_unique_and_statuses_known(self) -> None:
        ids = [str(row["id"]) for row in FACT_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        for row in FACT_ROWS:
            self.assertIn(row["status"], STATUSES)
            self.assertIn(row["slide"], ("да", "нет"))
            self.assertLessEqual(len(str(row["slide_line"])), SLIDE_LINE_MAX)
            self.assertTrue(row["claim"])
            self.assertTrue(row["value"])
            self.assertTrue(row["source"])

    def test_slide_lines_have_no_census_fingerprints(self) -> None:
        for row in FACT_ROWS:
            line = str(row["slide_line"])
            for token in JURY_FINGERPRINT_TOKENS:
                self.assertNotIn(token, line, msg=str(row["id"]))

    def test_no_verified_customer_when_pack_unprocessed(self) -> None:
        self.assertEqual(PUBLIC_UNPACK_CENSUS["processed"], False)
        customer = [row for row in FACT_ROWS if row["status"] == "VERIFIED_CUSTOMER"]
        self.assertEqual(customer, [])

    def test_ci_pin_matches_runtime_baseline(self) -> None:
        pin = _load_json("docs/evidence/runtime-baseline-latest.json")
        assert isinstance(pin, dict)
        facts = fact_by_id()
        backend = pin["backend"]
        frontend = pin["frontend"]
        self.assertEqual(
            str(facts["C-01"]["value"]),
            (
                f"{backend['tests_passed']} / {backend['tests_collected']} / "
                f"{backend['tests_failed']} / {backend['tests_skipped']}"
            ),
        )
        self.assertEqual(backend["tests_failed"], 0)
        self.assertEqual(frontend["tests_failed"], 0)
        self.assertEqual(
            str(facts["C-02"]["value"]),
            f"{frontend['tests_passed']} / {frontend['tests_failed']}",
        )
        self.assertEqual(pin["attestation"]["attested_by"], "ci")
        self.assertTrue(pin["publishable"])
        self.assertEqual(pin["corpus_kind"], "fixture")
        self.assertEqual(str(facts["C-04"]["value"]), "ci / true / fixture")

    def test_accuracy_rows_are_not_publishable(self) -> None:
        acc = _load_json("docs/evidence/accuracy-answer-2026-09.json")
        assert isinstance(acc, dict)
        self.assertFalse(acc["precision_claim_publishable"])
        self.assertFalse(acc["customer_go"])
        duplex = _load_json("docs/evidence/federated-clash-duplex-2026-08.json")
        assert isinstance(duplex, dict)
        self.assertEqual(duplex["runs"][0]["clash_count"], 837)
        self.assertFalse(duplex["closes_rt003"])

    def test_e1_e5_match_economics_file(self) -> None:
        text = (
            _REPO / "docs" / "partners" / "SAMOLET_CYCLE_ECONOMICS_ASSUMPTIONS_2026_09.md"
        ).read_text(encoding="utf-8")
        for needle in (E1_TEXT, E2_TEXT, E3_TEXT, E4_TEXT, E5_TEXT):
            self.assertIn(needle, text)
        self.assertEqual(fact_by_id()["A-11"]["value"], REPORT_PHRASE)

    def test_non_claim_count_matches_boundary(self) -> None:
        text = (_REPO / "docs" / "pilot-claim-boundary-2026.md").read_text(encoding="utf-8")
        self.assertEqual(_non_claim_count(text), NON_CLAIM_COUNT)

    def test_letter_asks_three_numbers_without_jargon(self) -> None:
        self.assertIn("рабочих дней", CUSTOMER_LETTER)
        self.assertIn("часов эксперт", CUSTOMER_LETTER)
        self.assertIn("лишних кругов", CUSTOMER_LETTER)
        self.assertNotIn("Wilson", CUSTOMER_LETTER)
        self.assertNotIn("IfcClash", CUSTOMER_LETTER)
        self.assertNotIn("customer_go", CUSTOMER_LETTER)
        self.assertEqual(len(DANGEROUS_QUESTIONS), 10)
        self.assertEqual(len(DEMO_20S), 5)
        self.assertIn("run_kt3_jury", " ".join(DEMO_20S))
        self.assertIn("1XYVUKGoDDbREfVxRKsHkl", " ".join(DEMO_20S))

    def test_auditor_markdown_lists_every_fact_and_is_not_a_jury_surface(self) -> None:
        self.assertTrue(_AUDITOR_MD.is_file())
        text = _AUDITOR_MD.read_text(encoding="utf-8")
        self.assertEqual(text, render_auditor_document())
        for row in FACT_ROWS:
            self.assertIn(f"| {row['id']} |", text, msg=str(row["id"]))
        for item in CONTRADICTIONS:
            self.assertIn(item["id"], text)
        for item in DANGEROUS_QUESTIONS:
            self.assertIn(item["id"], text)
        rel = "docs/quality/DEMO_DAY_AUDITOR_PACK_2026_09.md"
        self.assertNotIn(rel, JURY_SURFACES)
        for row in FACT_ROWS:
            if row["slide"] == "да":
                for token in ("2552", "6408", "10599"):
                    self.assertNotIn(token, str(row["slide_line"]))
        table = render_fact_table()
        self.assertIn("| A-01 |", table)
        self.assertIn("VERIFIED_INTERNAL", table)
        self.assertGreaterEqual(len(CONTRADICTIONS), 6)
        self.assertIn("claims-lint: allow-file", text.splitlines()[0])
        for token in JURY_FINGERPRINT_TOKENS:
            self.assertNotIn(token, " ".join(DEMO_20S))
