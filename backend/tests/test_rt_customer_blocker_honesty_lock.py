"""Honesty lock: RT-001/002/003 + ODA/MEP/OIDC stay customer-gated / stub-honest."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.architecture import PrecisionClaim, precision_claim_publishable_with_agreement
from aerobim.domain.cad_ingest import NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON
from aerobim.domain.system_capabilities import (
    build_auth_bff_capability,
    build_system_capabilities_payload,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.infrastructure.auth.oidc_bff_stubs import (
    InMemoryOidcBffStateStore,
    build_idp_authorize_url_draft,
    build_login_stub_payload,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


class CustomerBlockerHonestyLockTests(unittest.TestCase):
    def test_auth_bff_stays_not_implemented_with_pkce_field(self) -> None:
        payload = build_auth_bff_capability()
        self.assertEqual(payload["status"], "NOT_IMPLEMENTED")
        self.assertIn("phase_2_5_pkce", payload)

    def test_system_capabilities_forbid_mep_ok_and_native_dwg(self) -> None:
        caps = build_system_capabilities_payload()
        directions = caps["direction_contracts"]
        assert isinstance(directions, list)
        mep = next(c for c in directions if c["capability"] == "mep_system_graph")
        dwg = next(c for c in directions if c["capability"] == "native_dwg")
        self.assertNotEqual(mep["status"], "ok")
        self.assertEqual(dwg["status"], "missing")
        honesty = caps["honesty"]
        assert isinstance(honesty, dict)
        mep_clash = honesty["mep_system_clash"]
        assert isinstance(mep_clash, dict)
        self.assertNotEqual(mep_clash.get("status"), "ok")
        auth = caps["auth_bff"]
        assert isinstance(auth, dict)
        self.assertEqual(auth["status"], "NOT_IMPLEMENTED")

    def test_fixture_precision_not_publishable(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.99,
            corpus_id="fixture-1",
            corpus_kind="fixture",
            adjudicators=2,
            date="2026-08-11",
            held_out_split=True,
            fn_tracked=True,
        )
        self.assertFalse(claim.publishable)
        self.assertFalse(
            precision_claim_publishable_with_agreement(
                claim,
                agreement={
                    "pass_threshold_0_60": True,
                    "pass_alpha_0_67": True,
                    "krippendorff_alpha": 0.9,
                },
            )
        )

    def test_analyze_cad_ingestor_is_ezdxf_not_oda(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="rt-lock",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp) / "var",
                debug=True,
                oda_cad_enabled=True,
            )
            settings.storage_dir.mkdir(parents=True, exist_ok=True)
            container = bootstrap_container(settings)
            cad = container.resolve(Tokens.CAD_MODEL_INGESTOR)
            oda = container.resolve(Tokens.ODA_CAD_MODEL_INGESTOR)
            self.assertIsInstance(cad, EzdxfCadModelIngestor)
            self.assertIsInstance(oda, OdaCadModelIngestor)
            self.assertIsNot(type(cad), type(oda))
            result = OdaCadModelIngestor(enabled=True).ingest(Path(tmp) / "x.dwg")
            self.assertFalse(result.supported)
            self.assertEqual(result.reason, NATIVE_DWG_ODA_ENABLED_NO_SDK_REASON)


class OidcBffPhase25PkceTests(unittest.TestCase):
    def test_login_issues_pkce_without_exposing_verifier(self) -> None:
        store = InMemoryOidcBffStateStore()
        entry = store.issue(redirect_uri="https://app.example/cb")
        self.assertTrue(entry.code_verifier)
        self.assertTrue(entry.code_challenge)
        login = build_login_stub_payload(state_entry=entry)
        self.assertEqual(login["pkce"]["code_challenge_method"], "S256")
        self.assertEqual(login["pkce"]["code_challenge"], entry.code_challenge)
        self.assertNotIn("code_verifier", login)
        self.assertNotIn("code_verifier", login.get("pkce", {}))
        self.assertIsNone(login["idp_redirect_url"])
        self.assertEqual(login["status"], "NOT_IMPLEMENTED")

    def test_lab_env_builds_authorize_url_draft(self) -> None:
        store = InMemoryOidcBffStateStore()
        entry = store.issue(redirect_uri="https://app.example/cb")
        assert entry.code_challenge is not None
        # Without allowlist → no open redirect draft.
        blocked = build_login_stub_payload(
            state_entry=entry,
            authorize_endpoint="https://idp.example/oauth/authorize",
            client_id="aerobim-lab",
        )
        self.assertIsNone(blocked["idp_redirect_url"])
        self.assertFalse(blocked["redirect_uri_allowlisted"])
        login = build_login_stub_payload(
            state_entry=entry,
            authorize_endpoint="https://idp.example/oauth/authorize",
            client_id="aerobim-lab",
            redirect_uri_allowlist=("https://app.example/cb",),
        )
        url = login["idp_redirect_url"]
        self.assertIsInstance(url, str)
        self.assertIn("code_challenge=", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("nonce=", url)
        self.assertIn("client_id=aerobim-lab", url)
        self.assertEqual(login["status"], "NOT_IMPLEMENTED")
        self.assertTrue(login["redirect_uri_allowlisted"])
        draft = build_idp_authorize_url_draft(
            authorize_endpoint="https://idp.example/oauth/authorize",
            client_id="aerobim-lab",
            redirect_uri="https://app.example/cb",
            state=entry.state,
            code_challenge=entry.code_challenge,
            nonce=entry.nonce,
        )
        self.assertEqual(url, draft)


class WithoutSamoletProxySearchHonestyTests(unittest.TestCase):
    def test_public_proxy_search_does_not_close_rt_blockers(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "evidence"
            / "kt3-without-customer-2026-08.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("run_kt3_without_customer", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)

    def test_tz_proxy_rehearsal_doc_stays_no_go(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "evidence"
            / "tz-proxy-rehearsal-2026-08.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("Messick", text)
        self.assertNotIn("closes_rt001: true", text)


class JuryMikNovatorRedTeamHonestyTests(unittest.TestCase):
    def test_mik_sla_is_protocol_ready_not_measured_eng_ready(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "partners"
            / "MIK_PILOT_COMPLIANCE_2026.md"
        )
        text = path.read_text(encoding="utf-8")
        self.assertIn("PROTOCOL_READY", text)
        self.assertIn("BLOCKED_CUSTOMER_DATA", text)
        self.assertNotIn("ENG_READY | Числа выводимы", text)
        self.assertIn("просрочен", text)


_SPEECH_FORMULA_VERBATIM = (
    "Мы на стадии доработки. Одна команда показывает находку с доказательствами "
    "на учебном комплекте. Валидация эффективности и внедрение ещё не начались. "
    "`NO_GO` сохраняется, пока нет независимого размеченного корпуса, двух разметчиков, "
    "профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение) "
    "и подтверждения импорта в СОД."
)
_SPEECH_FORMULA_MARKERS = (
    "Мы на стадии доработки",
    "Одна команда показывает находку с доказательствами на учебном комплекте",
    "Валидация эффективности и внедрение ещё не начались",
    "`NO_GO` сохраняется, пока нет независимого размеченного корпуса",
    "профиля приёмки (публичные IDS экспертизы — измерение; подпись Самолёта — внедрение)",
)


class Kt2SpeechFormulaHonestyTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_speech_surfaces_use_formula_and_omit_contest_name(self) -> None:
        repo = self._repo()
        surfaces = (
            repo / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md",
            repo / "docs" / "docs.md",
            repo / "submission" / "03-presentation" / "slides.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            for marker in _SPEECH_FORMULA_MARKERS:
                self.assertIn(marker, text, msg=path.name)
            self.assertNotIn("Новатор", text, msg=path.name)
            self.assertNotIn("2259", text, msg=path.name)
            self.assertNotIn("25ef3ee", text, msg=path.name)
            self.assertNotIn("finding на fixture", text, msg=path.name)
            self.assertNotIn("live CLI с fail-closed", text, msg=path.name)
            self.assertNotIn("signed scope и CDE", text, msg=path.name)
        ru = (self._repo() / "README.ru.md").read_text(encoding="utf-8")
        self.assertIn("находку с доказательствами на учебном комплекте", ru)
        self.assertNotIn("finding на fixture", ru)
        self.assertNotIn("fail-closed доказатель", ru)

    def test_seven_jury_surfaces_carry_verbatim_formula(self) -> None:
        repo = self._repo()
        surfaces = (
            repo / "README.md",
            repo / "README.ru.md",
            repo / "docs" / "docs.md",
            repo / "docs" / "TIER0_INDEX.md",
            repo / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md",
            repo / "docs" / "pilot-claim-boundary-2026.md",
            repo / "submission" / "README.md",
            repo / "submission" / "01-repository" / "README.md",
            repo / "submission" / "02-documentation" / "README.md",
            repo / "submission" / "03-presentation" / "README.md",
            repo / "submission" / "03-presentation" / "slides.md",
            repo / "submission" / "04-prototype" / "README.md",
            repo / "submission" / "05-additional" / "README.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            self.assertIn(_SPEECH_FORMULA_VERBATIM, text, msg=path.as_posix())

    def test_kt2_video_is_withdrawn_not_promised(self) -> None:
        repo = self._repo()
        tier0 = (repo / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        presentation = (repo / "submission" / "03-presentation" / "README.md").read_text(
            encoding="utf-8"
        )
        for text, label in (
            (tier0, "TIER0"),
            (presentation, "presentation README"),
        ):
            self.assertIn("не записываем", text, msg=label)
            self.assertIn("не прилагаем", text, msg=label)
            self.assertNotIn("Оператор записывает 19.08", text, msg=label)

    def test_jury_memo_does_not_pin_a_stale_head_sha(self) -> None:
        text = (self._repo() / "docs" / "docs.md").read_text(encoding="utf-8")
        self.assertNotIn("HEAD `", text)
        self.assertIn("карточка речи", text)

    def test_aabb_fixture_n6_is_not_conflated_with_duplex_inventory(self) -> None:
        faq = (self._repo() / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("n=6", faq)
        self.assertIn("654", faq)
        self.assertIn("geometry_verified=false", faq)
        self.assertIn("Messick", faq)
        slice_readme = (
            self._repo() / "docs" / "evidence" / "clash-measurement-slice-2026-08" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("n=6", slice_readme)
        self.assertNotIn("n=5 (AABB", slice_readme)
        self.assertNotIn("at n=5", slice_readme)
        tri = (self._repo() / "docs" / "tz" / "KT2_TRI_SOURCE_ALIGNMENT_2026_08_12.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("AABB n=6 fixture", tri)
        self.assertNotIn("AABB n=5 fixture", tri)
        handoff = (
            self._repo() / "docs" / "evidence" / "kt2-handoff-2026-08-11" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("run_demo_ifc_acceptance_gate", handoff)
        self.assertIn("run_demo_vertical_slice", handoff)
        self.assertIn("AABB n=6", handoff)
        self.assertNotIn("AABB n=5", handoff)

    def test_tier0_states_kane_iua_freeze(self) -> None:
        text = (self._repo() / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Kane IUA", text)
        self.assertIn("f9389bf", text)
        self.assertIn("27/1026", text)
        self.assertIn("Intake-form", text)
        self.assertIn("Six desks", text)
        self.assertIn("Объект КТ#2", text)
        self.assertIn("Объект КТ#3", text)
        self.assertNotIn("Executable readiness = 5/5", text)

    def test_kt2_object_commit_card_is_on_jury_index(self) -> None:
        submission = (self._repo() / "submission" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Объект КТ#2", submission)
        self.assertIn("runtime-baseline-latest.json", submission)
        self.assertIn("attested_by=ci", submission)
        self.assertIn("f9389bf", submission)

    def test_jury_surfaces_omit_denylist_literals(self) -> None:
        import sys

        scripts = self._repo() / "scripts"
        sys.path.insert(0, str(scripts))
        try:
            from kitchen_denylist import load_tokens, verify_pin
        finally:
            if sys.path and sys.path[0] == str(scripts):
                sys.path.pop(0)
        tokens = load_tokens()
        verify_pin(tokens)
        surfaces = (
            self._repo() / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md",
            self._repo() / "docs" / "demo" / "KT3_JURY_FAQ_2026_08_25.md",
            self._repo() / "docs" / "demo" / "KT3_OPERATOR_RUNBOOK_2026_08_25.md",
            self._repo() / "docs" / "demo" / "KT3_TRACKER_DMITRY_2026_08.md",
            self._repo() / "docs" / "quality" / "INTERPRETATION_USE_LEDGER_2026_08.md",
            self._repo() / "docs" / "quality" / "OWNER_AI_PLAN_EXECUTION_2026_08_27.md",
            self._repo() / "backend" / "src" / "aerobim" / "domain" / "interpretation_use.py",
            self._repo() / "docs" / "TIER0_INDEX.md",
            self._repo() / "README.ru.md",
            self._repo() / "submission" / "README.md",
            self._repo() / "docs" / "tz" / "TRI_SOURCE_REQUIREMENTS_MATRIX_2026.md",
        )
        hits: list[str] = []
        for path in surfaces:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if any(token in text for token in tokens):
                hits.append(path.relative_to(self._repo()).as_posix())
        self.assertEqual(hits, [])

    def test_faq_separates_coverage_map_from_product_accuracy(self) -> None:
        text = (self._repo() / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("coverage_map_only", text)
        self.assertIn("16,7%", text)
        self.assertIn("не точность продукта", text)

    def test_tier0_red_teams_omit_local_pytest_count(self) -> None:
        repo = self._repo()
        surfaces = (
            repo / "docs" / "TIER0_INDEX.md",
            repo / "README.md",
            repo / "README.ru.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("2259", text, msg=path.name)

    def test_acceptance_profile_stays_unsigned(self) -> None:
        path = self._repo() / "docs" / "partners" / "SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("unsigned", text)
        self.assertIn("customer_pack_hash", text)
        self.assertNotIn("closes_rt001: true", text)

    def test_fixture_timing_sheet_is_not_customer_sla(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_FIXTURE_TIMING_2026_08_16.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("representative_scale=false", text)
        self.assertIn("Not ≤30 min SLA", text)
        self.assertIn("NO_GO", text)
        self.assertIn("sla_pass on the toy pack is not a claim", text)

    def test_ask_names_proxy_corpus_without_inventing_live_18_22(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_CORPUS_SSOT_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("27/1026", text)
        self.assertIn("18/22", text)
        self.assertIn("05.08", text)
        self.assertIn("NOT_RUN", text)

    def test_data_statement_does_not_close_rt001(self) -> None:
        path = self._repo() / "docs" / "evidence" / "DATA_STATEMENT_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("never customer evidence", text)
        self.assertIn("NOT_RUN", text)
        self.assertNotIn("closes_rt001: true", text)

    def test_unsigned_profile_keeps_blockers_open(self) -> None:
        profile = (
            self._repo() / "docs" / "partners" / "SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md"
        ).read_text(encoding="utf-8")
        self.assertIn("closes_rt002: false", profile)
        self.assertNotIn("closes_rt002: true", profile)
        self.assertIn("unsigned", profile)


class PersonasWave2Kt2PackHonestyTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_task07_comparison_does_not_adopt_competitor_accuracy(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_TASK07_COMPARISON_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("NO_GO", text)
        self.assertIn("не переносим как факт", text)
        self.assertIn("покажите методику", text)
        self.assertIn("NormaChecker", text)
        self.assertIn("WAIVE", text)
        self.assertIn("AIDOX", text)
        self.assertIn("AI Project Control", text)
        self.assertIn("fixture GT only", text)
        self.assertNotIn("closes_rt001: true", text)

    def test_corpus_ssot_frozen_until_kt2(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_CORPUS_SSOT_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn('frozen_until: "2026-08-20"', text)
        self.assertIn("27/1026", text)
        self.assertIn("18/22", text)
        self.assertIn("05.08", text)
        self.assertIn("NOT_RUN", text)
        self.assertIn("NO_GO", text)

    def test_10d_intake_is_proposed_boundary_not_cde_ready(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_10D_INTAKE_CONTRACT_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("project_id", text)
        self.assertIn("package_id", text)
        self.assertIn("revision", text)
        self.assertIn("rule_pack_id", text)
        self.assertIn("Not CDE-ready", text)
        self.assertIn("NO_GO", text)
        self.assertIn("AEROBIM_API_BEARER_TOKEN", text)

    def test_kt3_without_customer_stays_no_go(self) -> None:
        path = self._repo() / "docs" / "evidence" / "kt3-without-customer-2026-08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("re-scope", text)
        self.assertIn("2026-08-23", text)
        self.assertIn("NO_GO", text)
        self.assertIn("closes_rt001: false", text)
        self.assertIn("run_kt3_without_customer", text)
        self.assertIn("run_demo_ifc_acceptance_gate", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("валидация эффективности начата", text.lower())
        intake = (self._repo() / "audit" / "evidence" / "customer-intake-gate.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_kt3_without_customer", intake)
        self.assertIn("Do not wait for samples/customer/", intake)
        submission = (self._repo() / "submission" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Объект КТ#3", submission)
        self.assertIn("run_kt3_without_customer", submission)

    def test_alignment_f1_cell_is_fixture_qualified(self) -> None:
        path = self._repo() / "docs" / "samolet-techlab-alignment-2026.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("RU **fixture** ground truth", text)
        self.assertIn("macro F1 ≈ 0.86 (fixture-only; RT-001 OPEN", text)

    def test_tier0_lists_jury_artifacts(self) -> None:
        path = self._repo() / "docs" / "TIER0_INDEX.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("KT2_TASK07_COMPARISON_2026_08.md", text)
        self.assertIn("KT2_10D_INTAKE_CONTRACT_2026_08.md", text)
        self.assertIn("KT2_CORPUS_SSOT_2026_08.md", text)
        self.assertIn("KT3_JURY_FAQ_2026_08_25.md", text)
        self.assertIn("KT3_OPERATOR_RUNBOOK_2026_08_25.md", text)
        self.assertIn("KT3_TRACKER_DMITRY_2026_08.md", text)

    def test_qa_defense_stays_no_go_and_omits_contest_count(self) -> None:
        path = self._repo() / "docs" / "qa-defense-2026.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("точность на корпусе заказчика не заявляем", text.lower())
        self.assertNotIn("2259", text)
        self.assertNotIn("checkpoint go", text.lower())


def _pptx_plain_text(path: Path) -> str:
    ns = re.compile(r"<a:t[^>]*>(.*?)</a:t>", re.S)
    chunks: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/slide")
            and name.endswith(".xml")
            and "/_rels/" not in name
        ]
        names.sort(key=lambda item: int(re.search(r"slide(\d+)", item).group(1)))
        for name in names:
            xml = archive.read(name).decode("utf-8", errors="replace")
            chunks.extend(ns.findall(xml))
    return "\n".join(chunks)


def _git_ls_files(*args: str) -> str:
    git = shutil.which("git")
    if not git:
        raise unittest.SkipTest("git executable not found")
    return subprocess.check_output(
        [git, "ls-files", *args],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
    )


class JuryPackHygieneTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _is_tracked(self, rel: str) -> bool:
        return bool(_git_ls_files("--", rel).strip())

    def test_operator_kitchen_is_unpublished_from_git(self) -> None:
        forbidden = (
            "scripts/rewrite-author-konkovdv.sh",
            "scripts/git_commit.ps1",
            "scripts/fix_b5690_github_uid.ps1",
            "docs/architecture/ARCHITECTURE_REVIEW_BRIEF_2026_08.md",
            "docs/architecture/YANDEX_AI_STUDIO_AEROBIM_DEEP_ANALYSIS_2026_08_03.md",
            "docs/architecture/WORLD_PRACTICES_LITERATURE_REFRESH_2026_07_28.md",
            "docs/ai/LLM_COMPARATIVE_BENCHMARK.md",
            "docs/pilot/HARNESS_AND_DEMO_RUNBOOK_2026.md",
            "docs/partners/LETTER_OF_INTEREST_SAMOLET_TEMPLATE_2026_08.md",
            "docs/evidence/runtime-baseline-wave-a-windows-2026-08-15.md",
            "docs/evidence/kt2-handoff-2026-08-11/vertical-slice/report.html",
            "docs/gtm/SAMOLET_OSINT_VECTOR_KT2_2026_08_14.md",
            "docs/demo/TRACKER_MEETING_2026_08_14_FOLLOWUP.md",
            "docs/quality/RED_TEAM_REAUDIT2_2026_08_16.md",
            "docs/quality/RED_TEAM_ATOMIC4_2026_08_16.md",
            "docs/quality/RED_TEAM_ATOMIC5_2026_08_16.md",
            "docs/evidence/DATASET_HUNT_LOG_2026_08.md",
            "scripts/bootstrap_claims_allow_file.py",
        )
        for rel in forbidden:
            self.assertFalse(self._is_tracked(rel), msg=rel)

    def test_tracked_markdown_omits_ai_auditor_kitchen_fingerprints(self) -> None:
        listed = _git_ls_files("*.md")
        needles = (
            "ZCode",
            "rewrite-author-konkovdv",
            "эта машина",
            "Что делать ИИ дальше",
        )
        hits: list[str] = []
        repo = self._repo()
        for rel in listed.splitlines():
            rel = rel.strip().replace("\\", "/")
            if not rel:
                continue
            text = (repo / rel).read_text(encoding="utf-8")
            for needle in needles:
                if needle in text:
                    hits.append(f"{rel}: {needle}")
        self.assertEqual(hits, [])


_SUBMISSION_FIELDS = (
    "01-repository",
    "02-documentation",
    "03-presentation",
    "04-prototype",
    "05-additional",
)


class SubmissionPackHonestyTests(unittest.TestCase):
    """KT#2 submission folders mirror the intake form without inflating status."""

    def _submission(self) -> Path:
        return Path(__file__).resolve().parents[2] / "submission"

    def test_every_form_field_has_a_section(self) -> None:
        for field in _SUBMISSION_FIELDS:
            self.assertTrue((self._submission() / field / "README.md").is_file(), msg=field)

    def test_presentation_pack_has_slide_copy(self) -> None:
        slides = self._submission() / "03-presentation" / "slides.md"
        text = slides.read_text(encoding="utf-8")
        self.assertIn("NO_GO", text)
        self.assertIn("## Запрещено в кадре и в голосе", text)
        self.assertIn("требование → правило → объект → доказательство", text)
        self.assertIn("run_demo_ifc_acceptance_gate", text)
        self.assertIn("hidden holdout", text)
        self.assertIn("Не API 10D", text)
        self.assertNotIn("интегрированы с 10D", text.lower())

    def test_presentation_pack_tracks_main_deck(self) -> None:
        root = self._submission() / "03-presentation"
        pptx = root / "aerobim_kt2.pptx"
        pdf = root / "aerobim_kt2.pdf"
        self.assertTrue(pptx.is_file(), msg=str(pptx))
        self.assertTrue(pdf.is_file(), msg=str(pdf))
        tracked = _git_ls_files(
            "--",
            "submission/03-presentation/aerobim_kt2.pptx",
            "submission/03-presentation/aerobim_kt2.pdf",
        )
        self.assertIn("aerobim_kt2.pptx", tracked)
        self.assertIn("aerobim_kt2.pdf", tracked)
        deck = _pptx_plain_text(pptx).lower()
        self.assertIn("no_go", deck)
        self.assertIn("run_demo_ifc_acceptance_gate", deck)
        for needle in (
            "checkpoint go",
            ">90%",
            "mep delivered",
            "cde-ready",
            "native dwg",
        ):
            self.assertNotIn(needle, deck, msg=needle)

    def test_submission_surfaces_are_consistent_about_deck_and_video(self) -> None:
        deck = "aerobim_kt2.pptx"
        video_withdrawn = "не записываем"
        surfaces = (
            (self._submission() / "README.md", deck),
            (self._submission() / "01-repository" / "README.md", deck),
            (self._submission() / "02-documentation" / "README.md", deck),
            (self._submission() / "05-additional" / "README.md", deck),
            (self._submission() / "TZ_REQUIREMENTS_COVERAGE_2026_08.md", deck),
        )
        for path, needle in surfaces:
            text = path.read_text(encoding="utf-8")
            self.assertIn(needle, text, msg=path.name)
        presentation = (self._submission() / "03-presentation" / "README.md").read_text(
            encoding="utf-8"
        )
        tier0 = (self._submission().parent / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        for text, label in ((presentation, "03-presentation"), (tier0, "TIER0")):
            self.assertIn(video_withdrawn, text, msg=label)

    def test_github_community_health_files_exist(self) -> None:
        root = self._submission().parent
        for name in (
            "LICENSE",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SUPPORT.md",
            "MAINTAINERS.md",
            "CITATION.cff",
            ".github/CODEOWNERS",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            self.assertTrue((root / name).is_file(), msg=name)

    def test_submission_pack_keeps_checkpoint_no_go(self) -> None:
        index = (self._submission() / "README.md").read_text(encoding="utf-8")
        self.assertIn("NO_GO", index)
        self.assertIn("RT-001/002/003 OPEN", index)
        for field in _SUBMISSION_FIELDS:
            self.assertIn(field, index, msg=field)
        self.assertIn("Шесть столов", index)
        self.assertIn("доработка", index)

    def test_coverage_map_does_not_claim_tz_targets_as_measured(self) -> None:
        text = (self._submission() / "TZ_REQUIREMENTS_COVERAGE_2026_08.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("не измерено", text)
        self.assertIn("NO_GO", text)
        self.assertIn("n=6", text)
        self.assertIn("654", text)
        self.assertIn("f9389bf", text)
        self.assertIn("run_demo_ifc_acceptance_gate", text)
        # TZ targets may be quoted as customer criteria, never as our result.
        for forbidden in (
            "точность >90% достигнута",
            "SLA выполнен",
            "RT-001 CLOSED",
            "RT-002 CLOSED",
            "RT-003 CLOSED",
        ):
            self.assertNotIn(forbidden, text, msg=forbidden)

    def _tracked_paths(self) -> frozenset[Path]:
        repo = self._submission().parent
        paths: set[Path] = set()
        for line in _git_ls_files().splitlines():
            resolved = (repo / line).resolve()
            paths.add(resolved)
            paths.update(resolved.parents)
        return frozenset(paths)

    def test_repository_field_discloses_ci_pin(self) -> None:
        text = (self._submission() / "01-repository" / "README.md").read_text(encoding="utf-8")
        self.assertIn("runtime-baseline-latest.json", text)
        self.assertIn("attested_by=ci", text)
        self.assertIn("локальный pytest", text)

    def test_prototype_field_leads_with_acceptance_gate(self) -> None:
        text = (self._submission() / "04-prototype" / "README.md").read_text(encoding="utf-8")
        self.assertIn("run_demo_ifc_acceptance_gate", text)
        self.assertIn("run_demo_vertical_slice", text)
        self.assertIn("P1", text)

    def test_additional_field_has_six_desk_red_team(self) -> None:
        text = (self._submission() / "05-additional" / "README.md").read_text(encoding="utf-8")
        self.assertIn("шести столов", text)
        self.assertIn("INTERPRETATION_USE_LEDGER_2026_08.md", text)

    def test_submission_links_resolve_on_a_fresh_clone(self) -> None:
        # Resolve against tracked files: a gitignored local copy is not a published target.
        tracked = self._tracked_paths()
        pattern = re.compile(r"\]\((?!https?:|mailto:)([^)#]+)")
        broken: list[str] = []
        for path in sorted(self._submission().rglob("*.md")):
            for match in pattern.finditer(path.read_text(encoding="utf-8")):
                if (path.parent / match.group(1)).resolve() not in tracked:
                    broken.append(f"{path.name} -> {match.group(1)}")
        self.assertEqual(broken, [])


if __name__ == "__main__":
    unittest.main()
