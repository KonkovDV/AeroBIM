"""Demo-day speech lock stays TRL 4; open-bench clash is not customer MEP."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.deep_study_facts import PUBLIC_DEEP_STUDY
from aerobim.domain.demo_day_speech_lock import (
    AECV_IS_F1,
    AECV_VALUE,
    DUPLEX_CLASH_COUNT,
    DUPLEX_CORPUS,
    PUBLIC_IDS_FILES,
    PUBLIC_IDS_SPECS,
    RECOMMENDED_N,
    SEAT_OPTICS,
    SPACE_AREA_FROM_GEOMETRY,
    TRIAGE_ROWS,
    demo_day_speech_lock_snapshot,
    experiment_b_kr_share,
    ifcspace_total,
    licensed_slide_lines,
)
from aerobim.domain.mik_commission_scoring import FINALIST_CRITERIA, trl_5_claimed
from aerobim.domain.system_capabilities import build_four_direction_contracts
from aerobim.domain.unpack_census import PUBLIC_UNPACK_CENSUS

_REPO = Path(__file__).resolve().parents[2]


def _load_json(rel: str) -> object:
    raw = (_REPO / rel).read_text(encoding="utf-8")
    if raw.lstrip().startswith("<!--"):
        raw = raw.split("-->", 1)[1]
    return json.loads(raw)


class DemoDaySpeechLockTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = demo_day_speech_lock_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["customer_go"])
        self.assertFalse(snap["is_pack_processed"])
        self.assertFalse(snap["is_accuracy"])
        self.assertFalse(snap["trl_5_claimed"])
        self.assertFalse(trl_5_claimed())
        self.assertEqual(snap["trl_self_assess"], 4)
        self.assertFalse(snap["trl_claimed_on_cover"])
        self.assertEqual(snap["kill_count"], len(TRIAGE_ROWS))
        self.assertEqual(len(SEAT_OPTICS), 5)
        blob = json.dumps(snap)
        self.assertNotIn("pack_hash", blob)
        self.assertNotIn("sha256", blob)
        self.assertNotIn("УГТ-5", blob)
        self.assertNotIn("10599", blob)
        self.assertNotIn("6408", blob)
        self.assertNotIn("2552", blob)

    def test_ids_unique_and_docs_list_them(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        speech = (_REPO / "docs" / "demo" / "DEMO_DAY_SPEECH_LOCK_2026_09.md").read_text(
            encoding="utf-8"
        )
        redline = (_REPO / "docs" / "quality" / "DEMO_DAY_DECK_REDLINE_2026_09.md").read_text(
            encoding="utf-8"
        )
        slides = (_REPO / "submission" / "03-presentation" / "demo_day_slides.md").read_text(
            encoding="utf-8"
        )
        for row in TRIAGE_ROWS:
            self.assertIn(f"| {row['id']} |", redline, msg=row["id"])
            self.assertIn(row["id"], speech)
        self.assertIn("customer_go", speech)
        self.assertIn("TRL 4", slides)
        licensed_body = slides.split("## Запрещено", 1)[0]
        self.assertNotIn("УГТ-5", licensed_body)
        self.assertNotIn("macro F1 0,43", licensed_body)
        self.assertNotIn("macro F1 0.43", licensed_body)

    def test_carrier_math_matches_deep_study(self) -> None:
        pin = PUBLIC_DEEP_STUDY
        total = ifcspace_total()
        self.assertEqual(total, 16152)
        self.assertEqual(
            total,
            int(pin["ifcspace_pack_a"]) + int(pin["ifcspace_pack_b"]) + int(pin["ifcspace_pack_c"]),
        )
        snap = demo_day_speech_lock_snapshot()
        self.assertEqual(snap["ifcspace_total"], total)
        self.assertEqual(snap["netfloorarea_count"], 0)
        self.assertEqual(snap["ifcgrid_by_pack"], [0, 13, 53])
        self.assertEqual(snap["ifcreinforcingbar_count"], 0)
        self.assertEqual(snap["mep_duct_pipe_cable_count"], 0)
        self.assertEqual(snap["nwd_federation_count"], 3)
        self.assertEqual(snap["nwd_native"], "NOT_IMPLEMENTED")
        self.assertEqual(snap["ifc_schema"], "IFC2X3")

    def test_revision_duplicates_are_not_a_finding_class(self) -> None:
        census = PUBLIC_UNPACK_CENSUS
        self.assertEqual(census["unpacked_ifc_count"], 4)
        self.assertTrue(census["unpacked_ifc_are_wrapper_copies"])
        self.assertFalse(census["revision_duplicate_finding_class_pinned"])
        snap = demo_day_speech_lock_snapshot()
        self.assertFalse(snap["revision_duplicate_finding_class_pinned"])

    def test_open_bench_clash_is_not_customer(self) -> None:
        clash = json.loads(
            (_REPO / "docs" / "evidence" / "federated-clash-duplex-2026-08.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(clash["runs"][0]["clash_count"], DUPLEX_CLASH_COUNT)
        self.assertFalse(clash["closes_rt003"])
        snap = demo_day_speech_lock_snapshot()
        self.assertEqual(snap["duplex_clash_count"], 837)
        self.assertEqual(snap["duplex_corpus"], DUPLEX_CORPUS)
        self.assertIn("open_bench", snap["duplex_corpus"])

    def test_aecv_is_not_f1(self) -> None:
        aecv = _load_json("docs/evidence/aecv-bench-eval-latest.json")
        assert isinstance(aecv, dict)
        live = aecv["object_counting_live"]["summary"]
        self.assertAlmostEqual(live["macro_extended"], AECV_VALUE)
        self.assertFalse(AECV_IS_F1)
        snap = demo_day_speech_lock_snapshot()
        self.assertEqual(snap["aecv_metric"], "macro_extended")
        self.assertFalse(snap["aecv_is_f1"])
        self.assertEqual(snap["aecv_n_field_scores_extended"], 585)

    def test_sample_size_and_ids_and_kr(self) -> None:
        weekly = json.loads(
            (_REPO / "docs" / "evidence" / "weekly-eng-status-latest.json").read_text(
                encoding="utf-8"
            )
        )
        design = weekly["adjudication_corpus_plan"]
        self.assertEqual(design["power_design"]["n"], 62)
        self.assertEqual(design["recommended_n"], RECOMMENDED_N)
        self.assertEqual(PUBLIC_IDS_FILES, 50)
        self.assertEqual(PUBLIC_IDS_SPECS, 847)
        self.assertAlmostEqual(experiment_b_kr_share(), 4 / 24)
        snap = demo_day_speech_lock_snapshot()
        self.assertEqual(snap["recommended_n"], 111)
        self.assertEqual(snap["power_design_n"], 62)
        self.assertEqual(snap["moexp_ids_specs"], 389)
        self.assertEqual(snap["moexp_ids_files"], 24)
        self.assertNotEqual(snap["moexp_ids_specs"], snap["public_ids_specs"])
        self.assertEqual(snap["moscow_cim_selfcheck_start"], "2026-06-29")
        self.assertEqual(tuple(row[1] for row in FINALIST_CRITERIA), (30, 20, 20, 20, 10))
        self.assertFalse(snap["weights_pdf_in_git"])
        self.assertFalse(snap["mypy_file_count_in_ci_pin"])

    def test_space_area_from_geometry_is_not_implemented(self) -> None:
        self.assertEqual(SPACE_AREA_FROM_GEOMETRY, "not_implemented")
        by_name = {row["capability"]: row for row in build_four_direction_contracts()}
        self.assertEqual(by_name["space_area_from_geometry"]["status"], "not_implemented")
        src = (
            _REPO
            / "backend"
            / "src"
            / "aerobim"
            / "infrastructure"
            / "adapters"
            / "ifc_space_inventory.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(src)
        called = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertNotIn("create_shape", called)
        self.assertNotIn("tessellate", called)
        self.assertIn("NetFloorArea", src)

    def test_licensed_lines_do_not_overclaim(self) -> None:
        text = "\n".join(licensed_slide_lines()).lower()
        self.assertIn("trl 4", text)
        self.assertIn("not 5", text)
        self.assertIn("not f1", text)
        self.assertIn("not_verified", text)
        self.assertIn("501", text)
        self.assertNotIn("production-ready", text)
        self.assertNotIn("cde-ready", text)
        self.assertNotIn("mep delivered", text)

    def test_ci_pin_has_no_mypy_file_count(self) -> None:
        pin = json.loads(
            (_REPO / "docs" / "evidence" / "runtime-baseline-latest.json").read_text(
                encoding="utf-8"
            )
        )
        mypy = pin["quality_gates"]["mypy"]
        self.assertEqual(mypy["status"], "PASS")
        self.assertNotIn("files", mypy)
        self.assertEqual(pin["attestation"]["attested_by"], "ci")


if __name__ == "__main__":
    unittest.main()
