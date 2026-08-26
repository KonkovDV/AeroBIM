"""Public TZ v1 brief is not a product score and not the seven tasks."""

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path

from aerobim.domain.tz_v1_brief import (
    MIK_ACT_ACCURACY_HORIZON,
    PAPER_OBJECTS,
    PDF_SHA256,
    PILOT_INTERIM_PRECISION,
    TBD_IN_V1,
    mik_act_may_cite_tz_v1_accuracy_as_measured,
    v1_brief_snapshot,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVIDENCE = _REPO_ROOT / "docs" / "evidence" / "tz-v1-brief-coverage-2026-08.json"


class TzV1BriefTests(unittest.TestCase):
    def test_snapshot_stays_no_go_and_unmixed(self) -> None:
        snap = v1_brief_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertFalse(snap["pdf"]["binary_in_git"])
        self.assertFalse(snap["pdf"]["page_1_text_extractable"])
        self.assertEqual(snap["pdf"]["pages"], 6)
        self.assertEqual(snap["pdf"]["sha256"], PDF_SHA256)
        self.assertIn("techlab_seven_comparison_tasks", snap["not_the_same_as"])
        self.assertEqual(tuple(snap["paper_objects"]), PAPER_OBJECTS)

    def test_mik_act_does_not_cite_v1_gt90_as_measured(self) -> None:
        self.assertFalse(mik_act_may_cite_tz_v1_accuracy_as_measured())
        snap = v1_brief_snapshot()
        self.assertEqual(snap["evaluation"]["mik_act_horizon"], MIK_ACT_ACCURACY_HORIZON)
        self.assertEqual(snap["evaluation"]["pilot_interim_precision"], PILOT_INTERIM_PRECISION)
        self.assertFalse(snap["evaluation"]["product_score_published"])
        self.assertFalse(snap["evaluation"]["remark_quality_ru_en_measured"])
        self.assertFalse(snap["evaluation"]["cognitive_load_measured"])
        self.assertEqual(snap["evaluation"]["tz_v1_nonconformity_accuracy_target"], ">90%")

    def test_v1_tbd_has_v2_fill_docs(self) -> None:
        snap = v1_brief_snapshot()
        self.assertEqual(tuple(snap["tbd_in_v1"]), TBD_IN_V1)
        for key in TBD_IN_V1:
            self.assertIn(key, snap["tbd_filled_in_v2"])

    def test_v1_requirements_have_iua_hooks(self) -> None:
        ids = {row["id"] for row in v1_brief_snapshot()["requirements"]}
        self.assertEqual(len(ids), 16)
        self.assertTrue(ids.issuperset({"V1-01", "V1-04", "V1-10", "V1-12", "V1-16"}))

    def test_evidence_json_matches_snapshot(self) -> None:
        dumped = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(dumped, v1_brief_snapshot())

    def test_optional_owner_pdf_hash(self) -> None:
        raw = os.environ.get("AEROBIM_TZ_V1_PDF", "").strip()
        if not raw:
            self.skipTest("AEROBIM_TZ_V1_PDF not set")
        path = Path(raw)
        if not path.is_file():
            self.skipTest("AEROBIM_TZ_V1_PDF missing")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(digest, PDF_SHA256)


if __name__ == "__main__":
    unittest.main()
