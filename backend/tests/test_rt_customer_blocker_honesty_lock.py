"""Honesty lock: RT-001/002/003 + ODA/MEP/OIDC stay customer-gated / stub-honest."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
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
            / "datasets"
            / "RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("DEAD_CHANNEL", text)
        self.assertIn("клиентские данные", text.lower())
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


class AcademicRedTeamHonestyTests(unittest.TestCase):
    def test_academic_red_team_does_not_close_blockers_or_alias_proxies(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "quality"
            / "RED_TEAM_ACADEMIC_KT2_2026_08_15.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("Messick", text)
        self.assertIn("Kane", text)
        self.assertIn("Solihin", text)
        self.assertIn("ISO 19650", text)
        self.assertIn("Goodhart", text)
        self.assertIn("NOT_IMPLEMENTED", text)
        self.assertIn("Checkpoint stays **NO_GO**", text)
        self.assertIn("ACADEMIC_LITERATURE_TRIAGE_2026_08.md", text)
        self.assertIn("RT-ACAD-17", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)


class AcademicLiteratureTriageHonestyTests(unittest.TestCase):
    def test_literature_triage_does_not_close_blockers_or_run_harbor(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "quality"
            / "ACADEMIC_LITERATURE_TRIAGE_2026_08.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("Messick", text)
        self.assertIn("Kane", text)
        self.assertIn("2603.29199", text)
        self.assertIn("2605.01698", text)
        self.assertIn("2606.19544", text)
        self.assertIn("ISO 19650-6:2025", text)
        self.assertIn("IDS 1.1", text)
        self.assertIn("Harbor **NOT_RUN**", text)
        self.assertIn("Checkpoint stays **NO_GO**", text)
        self.assertIn("107043", text)
        self.assertIn("validate.buildingsmart.org", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)


class JuryMikNovatorRedTeamHonestyTests(unittest.TestCase):
    def test_jury_mik_novator_rt_does_not_close_blockers_or_skip_stage(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "quality"
            / "RED_TEAM_JURY_MIK_NOVATOR_KT2_2026_08_15.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("NO_GO", text)
        self.assertIn("доработка", text)
        self.assertIn("валидация эффективности", text.lower())
        self.assertIn("Лидеры инноваций", text)
        self.assertIn("Checkpoint stays **NO_GO**", text)
        self.assertIn("RT-JURY-K01", text)
        self.assertIn("RT-JURY-K02", text)
        self.assertIn("vertical-slice/report.html", text)
        self.assertNotIn("2259", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)

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


class FinalVerdictHonestyTests(unittest.TestCase):
    def test_final_verdict_stays_no_go_and_omits_unpublished_prompts(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "quality"
            / "RED_TEAM_FINAL_VERDICT_2026_08_16.md"
        )
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("closes_rt002: false", text)
        self.assertIn("closes_rt003: false", text)
        self.assertIn("Checkpoint stays **NO_GO**", text)
        self.assertIn("доработка", text)
        self.assertIn("KT2_HOSTILE_QA_PLAYBOOK", text)
        self.assertNotIn("docs/ai/MASTER_RED_TEAM_PROMPT_2026_08_16.md", text)
        self.assertNotIn("docs/quality/RED_TEAM_ATOMIC_2026_08_16.md", text)
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)


_SPEECH_FORMULA_MARKERS = (
    "Мы на стадии доработки",
    "Одна команда показывает live CLI",
    "Валидация эффективности и внедрение ещё не начались",
    "`NO_GO` сохраняется до корпуса Самолёта",
)


class Kt2SpeechFormulaHonestyTests(unittest.TestCase):
    def _repo(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def test_speech_surfaces_use_formula_and_omit_contest_name(self) -> None:
        repo = self._repo()
        surfaces = (
            repo / "docs" / "partners" / "PITCH_NOVALTOR_TECHLAB_2026_08.md",
            repo / "docs" / "demo" / "KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md",
            repo / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md",
            repo / "docs" / "docs.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            for marker in _SPEECH_FORMULA_MARKERS:
                self.assertIn(marker, text, msg=path.name)
            self.assertNotIn("Новатор", text, msg=path.name)
            self.assertNotIn("2259", text, msg=path.name)

    def test_tier0_red_teams_omit_local_pytest_count(self) -> None:
        repo = self._repo()
        surfaces = (
            repo / "docs" / "quality" / "RED_TEAM_ACADEMIC_KT2_2026_08_15.md",
            repo / "docs" / "quality" / "RED_TEAM_FUNDING_ATTACKS_KT2_2026_08_15.md",
            repo / "docs" / "ENGINEERING_STATUS_2026_08.md",
            repo / "README.md",
            repo / "README.ru.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("2259", text, msg=path.name)

    def test_customer_ask_names_four_intake_items(self) -> None:
        path = self._repo() / "docs" / "partners" / "SAMOLET_KT2_ASK_2026_08_15.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("adjudicators", text)
        self.assertIn("CDE", text)
        self.assertIn("pack_hash", text)
        self.assertNotIn("closes_rt001: true", text)

    def test_fixture_timing_sheet_is_not_customer_sla(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_FIXTURE_TIMING_2026_08_16.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("representative_scale=false", text)
        self.assertIn("Not ≤30 min SLA", text)
        self.assertIn("NO_GO", text)
        self.assertIn("sla_pass on the toy pack is not a claim", text)

    def test_ask_names_proxy_corpus_without_inventing_live_18_22(self) -> None:
        path = self._repo() / "docs" / "partners" / "SAMOLET_KT2_ASK_2026_08_15.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("27/1026", text)
        self.assertIn("18/22 от 05.08", text)
        self.assertIn("SKIPPED_PACK_INCOMPLETE", text)
        self.assertIn("NOT_RUN", text)
        self.assertIn("не «пересняли сегодня»", text)

    def test_data_statement_does_not_close_rt001(self) -> None:
        path = self._repo() / "docs" / "evidence" / "DATA_STATEMENT_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("never customer evidence", text)
        self.assertIn("NOT_RUN", text)
        self.assertNotIn("closes_rt001: true", text)

    def test_unsigned_profile_and_mik_ask_keep_blockers_open(self) -> None:
        repo = self._repo()
        profile = (
            repo / "docs" / "partners" / "SAMOLET_ACCEPTANCE_PROFILE_V0_1_2026_08_15.md"
        ).read_text(encoding="utf-8")
        mik = (repo / "docs" / "partners" / "MIK_OPERATOR_ASK_2026_08_15.md").read_text(
            encoding="utf-8"
        )
        for text in (profile, mik):
            self.assertIn("closes_rt002: false", text)
            self.assertNotIn("closes_rt002: true", text)
        self.assertIn("unsigned", profile)
        self.assertIn("VERIFY_WITH_OPERATOR", mik)
        self.assertIn("доработки", mik)


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

    def test_ask_names_owner_and_ack_deadline(self) -> None:
        path = self._repo() / "docs" / "partners" / "SAMOLET_KT2_ASK_2026_08_15.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("KonkovDV", text)
        self.assertIn("Сигиневич", text)
        self.assertIn("20.08.2026", text)
        self.assertIn("15.09", text)
        self.assertIn("closes_rt001: false", text)

    def test_plan_b_date_is_on_tracker_followup(self) -> None:
        path = self._repo() / "docs" / "demo" / "TRACKER_MEETING_2026_08_14_FOLLOWUP.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("15.09.2026", text)
        self.assertIn("re-scope", text)
        self.assertIn("Не kill сегодня", text)
        self.assertIn("NO_GO", text)

    def test_alignment_f1_cell_is_fixture_qualified(self) -> None:
        path = self._repo() / "docs" / "samolet-techlab-alignment-2026.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("RU **fixture** ground truth", text)
        self.assertIn("macro F1 ≈ 0.86 (fixture-only; RT-001 OPEN", text)

    def test_tier0_lists_wave2_artifacts(self) -> None:
        path = self._repo() / "docs" / "TIER0_INDEX.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("KT2_TASK07_COMPARISON_2026_08.md", text)
        self.assertIn("KT2_10D_INTAKE_CONTRACT_2026_08.md", text)
        self.assertIn("KT2_CORPUS_SSOT_2026_08.md", text)
        self.assertIn("KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md", text)

    def test_hostile_qa_playbook_pins_ssot_and_stays_no_go(self) -> None:
        path = self._repo() / "docs" / "demo" / "KT2_HOSTILE_QA_PLAYBOOK_2026_08_16.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("NO_GO", text)
        self.assertIn("schema 1.4.0", text)
        self.assertIn("порядок секунды", text)
        self.assertIn("KT2_TASK07_COMPARISON_2026_08.md", text)
        self.assertIn("KT2_CORPUS_SSOT_2026_08.md", text)
        self.assertIn("четыре пункта", text)
        self.assertIn("15.09", text)
        self.assertNotIn("2259", text)
        self.assertNotIn("开场", text)
        self.assertNotIn("开放", text)
        self.assertNotIn("yourselves", text)
        self.assertNotIn("1.3.0", text)
        self.assertNotIn("±0.5%", text)
        self.assertNotIn("11 пунктов", text)


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
        )
        for rel in forbidden:
            self.assertFalse(self._is_tracked(rel), msg=rel)


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
            ".github/repository-metadata.md",
        ):
            self.assertTrue((root / name).is_file(), msg=name)

    def test_submission_pack_keeps_checkpoint_no_go(self) -> None:
        index = (self._submission() / "README.md").read_text(encoding="utf-8")
        self.assertIn("NO_GO", index)
        self.assertIn("RT-001/002/003 OPEN", index)
        for field in _SUBMISSION_FIELDS:
            self.assertIn(field, index, msg=field)

    def test_coverage_map_does_not_claim_tz_targets_as_measured(self) -> None:
        text = (self._submission() / "TZ_REQUIREMENTS_COVERAGE_2026_08.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("не измерено", text)
        self.assertIn("NO_GO", text)
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
