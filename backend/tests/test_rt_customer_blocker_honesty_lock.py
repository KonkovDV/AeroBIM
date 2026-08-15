"""Honesty lock: RT-001/002/003 + ODA/MEP/OIDC stay customer-gated / stub-honest."""

from __future__ import annotations

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
        self.assertNotIn("closes_rt001: true", text)
        self.assertNotIn("closes_rt002: true", text)
        self.assertNotIn("closes_rt003: true", text)
        self.assertIn("Checkpoint stays **NO_GO**", text)


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
            repo / "docs" / "partners" / "_TECHLAB_2026_08.md",
            repo / "docs" / "demo" / "KT2_VIDEO_SCRIPT_3MIN_2026_08_19.md",
            repo / "docs" / "demo" / "KT2_JURY_FAQ_2026_08_12.md",
            repo / "docs" / "demo" / "KT2_HANDOFF_COVER_2026_08_11.md",
            repo / "docs" / "docs.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            for marker in _SPEECH_FORMULA_MARKERS:
                self.assertIn(marker, text, msg=path.name)
            self.assertNotIn("Новатор", text, msg=path.name)
            self.assertNotIn("2259", text, msg=path.name)

    def test_customer_ask_names_four_intake_items(self) -> None:
        path = self._repo() / "docs" / "partners" / "_08_15.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("closes_rt001: false", text)
        self.assertIn("adjudicators", text)
        self.assertIn("CDE", text)
        self.assertIn("pack_hash", text)
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


if __name__ == "__main__":
    unittest.main()
