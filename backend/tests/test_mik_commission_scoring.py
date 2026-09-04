
"""MIK commission arithmetic stays attributed and does not forecast a score."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.mik_commission_scoring import (
    AGGREGATION,
    ATTESTED_BY,
    CHECKPOINT,
    CRITERIA,
    ORDER_ID,
    PRIZE_FLOOR,
    TIE_BREAK_ORDER,
    criteria_max,
    k1_low_band_points,
    low_k1_high_rest_total,
    mik_staff_nominal_criteria_weight,
    partner_nominal_criteria_weight,
    predicted_aerobim_total,
    prize_floor_automatic_in_low_k1_high_rest,
    rest_high_band_points,
    scoring_snapshot,
)


class MikCommissionScoringTests(unittest.TestCase):
    def test_weights_sum_to_100_and_k1_is_largest(self) -> None:
        points = [item[1] for item in CRITERIA]
        self.assertEqual(sum(points), 100)
        self.assertEqual(criteria_max("K1"), 40)
        self.assertEqual(criteria_max("K2"), 20)
        self.assertEqual(criteria_max("K3"), 15)
        self.assertEqual(criteria_max("K4"), 15)
        self.assertEqual(criteria_max("K5"), 10)
        self.assertGreater(criteria_max("K1"), criteria_max("K2"))
        self.assertGreater(
            criteria_max("K1"),
            criteria_max("K3") + criteria_max("K4"),
        )

    def test_k2_and_k5_together_are_only_thirty(self) -> None:
        self.assertEqual(criteria_max("K2") + criteria_max("K5"), 30)

    def test_partner_and_mik_nominal_criteria_weights(self) -> None:
        self.assertEqual(partner_nominal_criteria_weight(), 65)
        self.assertEqual(mik_staff_nominal_criteria_weight(), 35)
        snap = scoring_snapshot()
        self.assertEqual(snap["partner_nominal_criteria_weight"], 65)
        self.assertEqual(snap["mik_staff_nominal_criteria_weight"], 35)
        self.assertIn("seat_playbook", snap)
        self.assertIn("mik_operator_letter", snap)
        repo = Path(__file__).resolve().parents[2]
        self.assertTrue((repo / snap["seat_playbook"]).is_file())
        self.assertTrue((repo / snap["mik_operator_letter"]).is_file())

    def test_aggregation_is_mean_and_novelty_is_not_tie_break(self) -> None:
        from aerobim.domain.mik_commission_scoring import FINALIST_AGGREGATION

        self.assertEqual(AGGREGATION, "arithmetic_mean")
        self.assertEqual(FINALIST_AGGREGATION, "sum")
        self.assertEqual(TIE_BREAK_ORDER, ("K3", "K4"))
        self.assertNotIn("K2", TIE_BREAK_ORDER)
        self.assertNotIn("K1", TIE_BREAK_ORDER)

    def test_low_k1_high_rest_does_not_auto_clear_prize_floor(self) -> None:
        k1_lo, k1_hi = k1_low_band_points()
        self.assertAlmostEqual(k1_lo, 8.4)
        self.assertAlmostEqual(k1_hi, 16.0)
        rest_lo, rest_hi = rest_high_band_points()
        self.assertAlmostEqual(rest_lo, 36.6)
        self.assertAlmostEqual(rest_hi, 48.0)
        total_lo, total_hi = low_k1_high_rest_total()
        self.assertAlmostEqual(total_lo, 45.0)
        self.assertAlmostEqual(total_hi, 64.0)
        self.assertEqual(PRIZE_FLOOR, 50)
        self.assertLess(total_lo, PRIZE_FLOOR)
        self.assertGreater(total_hi, PRIZE_FLOOR)
        self.assertFalse(prize_floor_automatic_in_low_k1_high_rest())

    def test_snapshot_stays_no_go_and_does_not_forecast(self) -> None:
        snap = scoring_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertEqual(snap["attested_by"], ATTESTED_BY)
        self.assertEqual(snap["order_id"], ORDER_ID)
        self.assertFalse(snap["fund_pdf_in_git"])
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["partner_seats_guaranteed"])
        self.assertFalse(snap["novelty_in_tie_break"])
        self.assertTrue(snap["application_roster_is_k1_object"])
        self.assertFalse(snap["oral_advisors_score_k1"])
        self.assertIsNone(snap["predicted_aerobim_total"])
        self.assertIsNone(predicted_aerobim_total())
        self.assertEqual(snap["quorum_min_members"], 3)
        self.assertEqual(snap["k2_plus_k5_max"], 30)

    def test_system_b_weights_and_b1_only_tie_break(self) -> None:
        from aerobim.domain.mik_commission_scoring import (
            COMMISSION_NUMBER,
            FINALIST_CRITERIA,
            FINALIST_TIE_BREAK_ORDER,
            TASK_APPENDIX_4_NUMBER,
            confirmed_partner_validation_metrics,
            finalist_criteria_max,
            partner_kpis_agreed_in_writing,
        )

        points = [item[1] for item in FINALIST_CRITERIA]
        self.assertEqual(sum(points), 100)
        self.assertEqual(finalist_criteria_max("B1"), 30)
        self.assertEqual(finalist_criteria_max("B2"), 20)
        self.assertEqual(finalist_criteria_max("B5"), 10)
        self.assertEqual(FINALIST_TIE_BREAK_ORDER, ("B1",))
        self.assertNotIn("K3", FINALIST_TIE_BREAK_ORDER)
        self.assertFalse(confirmed_partner_validation_metrics())
        self.assertFalse(partner_kpis_agreed_in_writing())
        snap = scoring_snapshot()
        self.assertEqual(snap["task_appendix_4_number"], TASK_APPENDIX_4_NUMBER)
        self.assertEqual(snap["commission_number"], COMMISSION_NUMBER)
        self.assertFalse(snap["speak_handout_label_as_regulation"])
        self.assertTrue(snap["prize_floor_wording_is_ambiguous"])
        self.assertIsNone(snap["predicted_aerobim_total"])
        self.assertFalse(snap["git_raises_k1"])
        self.assertFalse(snap["gost_42001_certified"])
        self.assertFalse(snap["city_pilot_is_techlab_prize"])
        self.assertIn("etu.ru", snap["appendix_4_public_source"])
        self.assertEqual(snap["task_appendix_4_number"], 6)
        self.assertEqual(snap["aggregation"], "arithmetic_mean")
        self.assertEqual(snap["finalist_aggregation"], "sum")
        self.assertEqual(snap["system_a"], "regulation_appendix_2_via_order_protocol_form")
        self.assertEqual(snap["system_b"], "regulation_appendix_3_unseen")
        self.assertFalse(snap["regulation_appendix_3_in_git"])
        self.assertFalse(snap["finalist_weights_are_regulation_appendix_3"])
        self.assertFalse(snap["prize_floor_denominator_known"])

    def test_low_k1_top_plus_rest_high_lo_clears_floor_identity(self) -> None:
        from aerobim.domain.mik_commission_scoring import (
            k1_ten_people_required,
            k3_equals_validation_metrics,
            reachable_inside_low_k1_if_rest_high,
            trl_5_claimed,
        )

        k1_lo, k1_hi = k1_low_band_points()
        rest_lo, _rest_hi = rest_high_band_points()
        self.assertAlmostEqual(k1_hi, 16.0)
        self.assertAlmostEqual(k1_hi + rest_lo, 52.6)
        self.assertTrue(reachable_inside_low_k1_if_rest_high())
        self.assertFalse(k1_ten_people_required())
        self.assertFalse(k3_equals_validation_metrics())
        self.assertFalse(trl_5_claimed())
        snap = scoring_snapshot()
        self.assertEqual(snap["min_team_size"], 1)
        self.assertEqual(snap["max_team_size"], 10)
        self.assertEqual(snap["trl_self_assess"], 4)
        self.assertFalse(snap["trl_5_claimed"])
        self.assertFalse(snap["independent_ogt_performed"])
        self.assertFalse(snap["k4_revenue_claimed"])
        self.assertFalse(snap["pnst_841_certified"])
        self.assertFalse(snap["foreign_labor_cut_as_ours"])
        self.assertFalse(snap["sponsor_quote_is_commission_chair"])
        self.assertFalse(snap["tam_horizon_is_our_revenue"])
        self.assertFalse(snap["k4_asks_customer_capex"])
        self.assertFalse(snap["k4_offsets_partner_ifrs_loss"])
        self.assertFalse(snap["ras_ifrs_signs_are_the_same"])
        self.assertFalse(snap["catalog_four_are_all_applicants"])
        self.assertFalse(snap["peer_card_claims_externally_verified"])
        self.assertLess(k1_lo + rest_lo, PRIZE_FLOOR)

    def test_ssot_does_not_mint_a_score_or_certify_gost(self) -> None:
        source = Path(__file__).resolve().parents[1]
        scoring = (source / "src" / "aerobim" / "domain" / "mik_commission_scoring.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("attested_by=ci", scoring)
        self.assertNotIn("predicted_aerobim_total =", scoring)
        self.assertIn("owner_briefing", scoring)


class Kt3CommissionPackTests(unittest.TestCase):
    _repo = Path(__file__).resolve().parents[2]

    def test_economic_assumptions_file_has_empty_hours(self) -> None:
        path = self._repo / "docs" / "partners" / "ECONOMIC_MODEL_LABELED_ASSUMPTIONS_2026_08.md"
        text = path.read_text(encoding="utf-8").lower()
        self.assertIn("нет данных", text)
        self.assertIn("a1", text)
        self.assertIn("a8", text)
        self.assertNotIn("сертифицирован", text)

    def test_bom_and_fixture_cover_exist(self) -> None:
        bom = self._repo / "docs" / "quality" / "KT3_DELIVERY_BOM_2026_08.md"
        cover = self._repo / "docs" / "quality" / "KT3_FIXTURE_VALIDATION_COVER_2026_08.md"
        bom_text = bom.read_text(encoding="utf-8").lower()
        cover_text = cover.read_text(encoding="utf-8").lower()
        self.assertIn("mit", bom_text)
        self.assertIn("не входит", bom_text)
        self.assertIn("is_representative=false", cover_text)
        self.assertIn("attested_by=ci", cover_text)
        self.assertIn("no_go", cover_text)

    def test_evidence_map_and_gost_stack_are_findable(self) -> None:
        from aerobim.domain.mik_commission_scoring import (
            city_pilot_is_techlab_prize,
            git_raises_k1,
            gost_42001_certified,
        )

        self.assertFalse(git_raises_k1())
        self.assertFalse(gost_42001_certified())
        self.assertFalse(city_pilot_is_techlab_prize())
        evidence = self._repo / "docs" / "quality" / "MIK_CRITERION_EVIDENCE_MAP_2026_08.md"
        gost = self._repo / "docs" / "quality" / "NATIONAL_AI_GOST_STACK_KT3_2026.md"
        k1 = self._repo / "docs" / "partners" / "K1_ROLE_MATRIX_TEMPLATE_2026_08.md"
        evidence_text = evidence.read_text(encoding="utf-8")
        gost_text = gost.read_text(encoding="utf-8")
        k1_text = k1.read_text(encoding="utf-8")
        for code in ("| К1 |", "| К5 |", "| Б1 |", "| Б5 |"):
            self.assertIn(code, evidence_text)
        self.assertIn("predicted_aerobim_total() is None", evidence_text)
        self.assertIn("K4_COMMERCIAL_PATH_2026_08.md", evidence_text)
        self.assertIn("K2_NOVELTY_VS_PEERS_2026_08.md", evidence_text)
        self.assertIn("i.moscow/pilot", evidence_text)
        self.assertIn("1549-ст", gost_text)
        self.assertIn("1550-ст", gost_text)
        self.assertIn("1539-ст", gost_text)
        self.assertIn("1548-ст", gost_text)
        self.assertIn("не сертификат", gost_text.lower())
        self.assertIn("42001", gost_text)
        self.assertIn("совместимость не сертификация", gost_text.lower())
        self.assertIn("пустые", k1_text.lower())
        for line in k1_text.splitlines():
            if not line.startswith("|"):
                continue
            if "Роль" in line or "---" in line:
                continue
            cells = [cell.strip() for cell in line.split("|")]
            # leading empty + role, class, who, evidence, git, trailing empty
            self.assertGreaterEqual(len(cells), 5, msg=line)
            self.assertEqual(cells[3], "", msg=line)

    def test_ssot_source_does_not_encode_a_chat_score(self) -> None:
        scoring = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "domain"
            / "mik_commission_scoring.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("32.6", scoring)
        self.assertNotIn("24.6", scoring)
        self.assertNotIn("32.7", scoring)

    def test_levers_trl_and_k3_fit_docs_exist(self) -> None:
        levers = self._repo / "docs" / "quality" / "MIK_A_LEVERS_PAST_50_2026_08.md"
        trl = self._repo / "docs" / "quality" / "TRL_GOST_R_58048_SELF_ASSESS_2026.md"
        k3 = self._repo / "docs" / "quality" / "K3_PARTNER_FIT_TICKSHEET_2026_08.md"
        levers_text = levers.read_text(encoding="utf-8")
        trl_text = trl.read_text(encoding="utf-8").lower()
        k3_text = k3.read_text(encoding="utf-8").lower()
        self.assertIn("52,6", levers_text)
        self.assertIn("от 1 до 10", levers_text)
        self.assertIn("угт 4", trl_text)
        self.assertIn("не заявляем угт 5", trl_text)
        self.assertIn("независимая команда огт", trl_text)
        self.assertIn("не метрики б2", k3_text)
        self.assertIn("k3_equals_validation_metrics() == false", k3_text)

    def test_k4_k2_pnst_seats_and_paste_exist(self) -> None:
        from aerobim.domain.mik_commission_scoring import (
            catalog_four_are_all_applicants,
            foreign_labor_cut_as_ours,
            k4_asks_customer_capex,
            k4_offsets_partner_ifrs_loss,
            k4_revenue_claimed,
            peer_card_claims_externally_verified,
            pnst_841_certified,
            ras_ifrs_signs_are_the_same,
            regulation_appendix_3_in_git,
            sponsor_quote_is_commission_chair,
            tam_horizon_is_our_revenue,
        )

        self.assertFalse(k4_revenue_claimed())
        self.assertFalse(pnst_841_certified())
        self.assertFalse(foreign_labor_cut_as_ours())
        self.assertFalse(sponsor_quote_is_commission_chair())
        self.assertFalse(tam_horizon_is_our_revenue())
        self.assertFalse(k4_asks_customer_capex())
        self.assertFalse(k4_offsets_partner_ifrs_loss())
        self.assertFalse(ras_ifrs_signs_are_the_same())
        self.assertFalse(catalog_four_are_all_applicants())
        self.assertFalse(peer_card_claims_externally_verified())
        self.assertFalse(regulation_appendix_3_in_git())
        k4 = (
            (self._repo / "docs" / "quality" / "K4_COMMERCIAL_PATH_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        k2 = (
            (self._repo / "docs" / "quality" / "K2_NOVELTY_VS_PEERS_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        pnst = (
            (self._repo / "docs" / "quality" / "PNST_841_AI_QUALITY_EVAL_2026.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        seats = (self._repo / "docs" / "quality" / "MIK_SEAT_BRIEFS_2026_08.md").read_text(
            encoding="utf-8"
        )
        paste = (
            (self._repo / "docs" / "partners" / "I_MOSCOW_APPLICATION_PASTE_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        cover = (
            (self._repo / "docs" / "partners" / "PARTNER_PROTOCOL_SIGNREADY_COVER_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        self.assertIn("10,1 млрд", k4)
        self.assertIn("не наш sam", k4)
        self.assertIn("72,1", k4)
        self.assertIn("не переносить как эффект aerobim", k4)
        self.assertIn("500 млн", k4)
        self.assertIn("ablation", k2)
        self.assertIn("не переносить как наши", k2)
        self.assertIn("61-пнст", pnst)
        self.assertIn("не оценка", pnst)
        self.assertIn("Пилотирование Фонда", seats)
        self.assertIn("Информационное моделирование", seats)
        self.assertIn("два класса", paste)
        self.assertIn("0,60", cover)
        self.assertIn("не цифра тз", cover)
        self.assertIn("не прогноз нашего балла", paste)
        self.assertIn("tam_horizon_is_our_revenue() == false", k4)
        self.assertIn("нулевой вход", k4)
        self.assertIn("не capex", k4)
        self.assertIn("мсфо", k4)
        self.assertIn("рсбу", k4)
        self.assertIn("k4_asks_customer_capex() == false", k4)
        self.assertIn("четыре пункта", k2)
        self.assertIn("не проверены извне", k2)
        thresholds = (
            (self._repo / "docs" / "quality" / "CUSTOMER_THRESHOLD_VS_ACTUAL_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        self.assertIn("256", thresholds)
        self.assertIn("0,86", thresholds)
        self.assertIn("не поднимаем", thresholds)
        scoring = (
            (self._repo / "docs" / "quality" / "MIK_COMMISSION_SCORING_2026_08.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        self.assertIn("итоговая сумма", scoring)
        self.assertIn("приложение 3 к положению", scoring)
        self.assertIn("не видели", scoring)

    def test_system_b_ticksheet_exists_and_does_not_forecast(self) -> None:
        from aerobim.domain.mik_commission_scoring import B_FINAL_TICKSHEET

        path = self._repo / B_FINAL_TICKSHEET
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("predicted_aerobim_total() is none", lower)
        self.assertIn("| б1 | 30 |", lower)
        self.assertIn("| б2 | 20 |", lower)
        self.assertIn("| б5 | 10 |", lower)
        self.assertIn("только **б1**", lower)
        self.assertIn("не прогноз", lower)
        self.assertNotIn("closes_rt001: true", lower)
        snap = scoring_snapshot()
        self.assertEqual(snap["b_final_ticksheet"], B_FINAL_TICKSHEET)
        self.assertIsNone(snap["predicted_aerobim_total"])

    def test_system_b_pack_docs_stay_honest(self) -> None:
        from aerobim.domain.mik_commission_scoring import (
            ADR_004_PRIZE_IP,
            DEFECT_INJECTION_PLAN,
            LAB_BEFORE_AFTER,
            ORDER_WEIGHTS_VERIFICATION,
            OWNER_ACTIONS,
        )

        snap = scoring_snapshot()
        self.assertIsNone(snap["predicted_aerobim_total"])
        lab = (self._repo / LAB_BEFORE_AFTER).read_text(encoding="utf-8").lower()
        inj = (self._repo / DEFECT_INJECTION_PLAN).read_text(encoding="utf-8").lower()
        adr = (self._repo / ADR_004_PRIZE_IP).read_text(encoding="utf-8").lower()
        weights = (self._repo / ORDER_WEIGHTS_VERIFICATION).read_text(encoding="utf-8").lower()
        owner = (self._repo / OWNER_ACTIONS).read_text(encoding="utf-8").lower()
        faq = (
            (self._repo / "docs" / "demo" / "KT3_JURY_FAQ_2026_08_25.md")
            .read_text(encoding="utf-8")
            .lower()
        )
        tier0 = (self._repo / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        exp_b = (
            (
                self._repo
                / "docs"
                / "evidence"
                / "EXPERIMENT_B_TYPICAL_REMARKS_KR_COVERAGE_2026_08.md"
            )
            .read_text(encoding="utf-8")
            .lower()
        )
        env_var = (
            self._repo / "docs" / "quality" / "ENV_VAR_BIDIRECTIONAL_INVENTORY_2026_08.md"
        ).read_text(encoding="utf-8")
        self.assertIn("не б4 партнёра", lab)
        self.assertIn("не корпус заказчика", lab)
        self.assertIn("synthetic_only", inj)
        self.assertIn("20260824", inj)
        self.assertIn("переносится на комплект", inj)
        self.assertIn("evaluate_injection_recall", inj)
        self.assertIn("**proposed.**", adr)
        self.assertIn("license", adr)
        self.assertIn("unverified", weights)
        self.assertIn("| **unverified** |", weights)
        self.assertIn("attested_by=owner_briefing", weights)
        self.assertIn("не утверждает, что действие уже сделано", owner)
        self.assertIn("oa-1", owner)
        self.assertIn("угт 4", faq)
        self.assertIn("не заявляем", faq)
        self.assertIn("02.04.2026", faq)
        self.assertIn("сто самолёта", faq)
        self.assertIn("не измерялось", faq)
        self.assertIn("B_FINAL_SCORING_TICKSHEET_2026_09.md", tier0)
        self.assertIn("BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md", tier0)
        self.assertIn("RELATED_WORK_PREPRINT_2026_09.md", tier0)
        self.assertIn("lab-before-after-fixture-tool-only-latest.json", lab)
        self.assertIn("DEFECT_INJECTION_RECALL_PLAN_2026_09.md", tier0)
        self.assertIn("ADR-004-prize-ip-mit-fork-2026.md", tier0)
        self.assertIn("ORDER_WEIGHTS_VERIFICATION_2026_09.md", tier0)
        self.assertNotIn("OWNER_ACTIONS_2026_09.md", tier0)
        self.assertIn("#2/#4 уже входят", exp_b)
        self.assertNotIn("2694", env_var)
        for rel in (
            LAB_BEFORE_AFTER,
            DEFECT_INJECTION_PLAN,
            ADR_004_PRIZE_IP,
            ORDER_WEIGHTS_VERIFICATION,
            OWNER_ACTIONS,
            "docs/quality/B_FINAL_SCORING_TICKSHEET_2026_09.md",
        ):
            text = (self._repo / rel).read_text(encoding="utf-8").lower()
            self.assertIn("closes_rt001: false", text)
            self.assertNotIn("closes_rt001: true", text)
            self.assertNotIn("closes_rt002: true", text)
            self.assertNotIn("closes_rt003: true", text)


if __name__ == "__main__":
    unittest.main()
