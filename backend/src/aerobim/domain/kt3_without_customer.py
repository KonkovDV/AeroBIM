"""KT#3 without Samolet files: re-scope is the product decision, not a wait state.

Does not close RT-001/002/003. Does not publish product accuracy.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO, GO_KIND
from aerobim.domain.intake_gate_keys import INTAKE_GATE_KEYS
from aerobim.domain.kt3_jury import JURY_COMMAND
from aerobim.domain.rt_blocker_volumes import assemble_rt_blocker_volumes
from aerobim.domain.tracker_eight_tasks import tracker_eight_snapshot
from aerobim.domain.tracker_six_tasks import tracker_snapshot
from aerobim.domain.tz_v1_brief import PAPER_OBJECTS

PLAN_B_DECISION: Final = "re-scope"
OWNER_DECISION_DATE: Final = "2026-08-23"
PROGRAM_FORK_DATE: Final = "2026-09-15"
CLAIM_LEVEL: Final = "fixture_and_proxy_only"
DEMO_COMMAND: Final = "python -m aerobim.tools.run_demo_ifc_acceptance_gate"
PACK_COMMAND: Final = "python -m aerobim.tools.run_kt3_without_customer"
JURY_PACK_COMMAND: Final = JURY_COMMAND
SCHEMA_VERSION: Final = "1.6.0"

CLAIM_BOUNDARY: Final = (
    "Customer files are not expected in git. "
    "KT#3 is the live fixture gate plus public/synthetic proxies. "
    "Measurement volumes (RT-001a content pairing, RT-001 protocol rehearsal, "
    "RT-002a public IDS, RT-002b channel EIR/BIM-standard text, RT-003a planted "
    "geometric clash, RT-003b IfcSystem graph rehearsal, RT-003 NWD federation "
    "carrier) use substitutes. "
    "Not product accuracy. Not customer SLA. Not MEP delivered. "
    "Not CDE-ready. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false). closes_rt001/002/003 stay false."
)

REQUIRED_EVIDENCE: Final[tuple[tuple[str, str], ...]] = (
    ("demo_manifest", "samples/demo/vertical-slice-2026-08-11/manifest.json"),
    (
        "synthetic_label_freeze",
        "samples/benchmarks/rt001-preregistration-synthetic-freeze-2026-08-14.json",
    ),
    ("jurisdiction_ids_pointer", "samples/ids/moexp/jurisdiction-profile-pointer.json"),
    ("corpus_ssot", "docs/demo/KT2_CORPUS_SSOT_2026_08.md"),
    ("tz_proxy_rehearsal", "docs/evidence/tz-proxy-rehearsal-2026-08.md"),
    ("planted_federated_clash", "docs/evidence/federated-clash-planted-2026-08.md"),
    ("intake_gate", "audit/evidence/customer-intake-gate.json"),
    ("tz_v2", "docs/tz/TZ_SAMOLET_TECHLAB_TASK_07_V2_2026.md"),
    ("moscow_agr_ruler", "samples/norm-packs/moscow_agr_2026/pack.json"),
    ("kt3_jury_card", "docs/demo/KT3_JURY_FAQ_2026_08_25.md"),
    ("kt3_operator_runbook", "docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md"),
    ("kt3_tracker_card", "docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md"),
    (
        "kt3_tracker_eight",
        "docs/quality/TRACKER_EIGHT_TASKS_2026_08.md",
    ),
    ("tz_v1_brief", "docs/tz/TZ_V1_CONTEST_BRIEF_PIN_2026_08.md"),
    ("owner_ai_plan", "docs/quality/OWNER_AI_PLAN_EXECUTION_2026_08_27.md"),
    ("iua_ledger", "docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md"),
    (
        "typical_errors_catalog",
        "samples/benchmarks/samolet-typical-errors-catalog.json",
    ),
    ("rt_blocker_volumes", "docs/evidence/rt-blocker-volumes-2026-09.md"),
    ("rt001_dual_rater_simulation", "docs/evidence/rt001-dual-rater-simulation-2026-09.md"),
    ("oos_qto", "samples/oos/qto_space_area.unsigned.json"),
)

TZ_MVP_DEMONSTRABLE: Final[tuple[str, ...]] = (
    "TR-3 IFC geometry/attributes",
    "TR-8 IDS checking",
    "TR-20 problem_zone",
    "TR-21 template remarks RU/EN",
    "TR-22 HITL edit/confirm/reject",
    "TR-25 clean-architecture layers",
    "TR-27 DeterminismGate",
    "TR-29 capability honesty",
    "TR-43 reproducible demo path",
)

TZ_EXPLICIT_GAPS: Final[tuple[str, ...]] = (
    "TR-6 native DWG",
    "TR-13 calculation_correctness",
    "TR-15 mep_system_clash",
    "TR-17 unsigned space-efficiency metric",
    "TR-48 publishable product accuracy >90%",
    "TR-49 customer SLA",
)


class Kt3WithoutCustomerError(ValueError):
    """Payload or inventory is not an honest no-customer KT#3 pack."""


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise Kt3WithoutCustomerError(f"expected JSON object in {path}")
    return data


def inventory_required_evidence(repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role, rel in REQUIRED_EVIDENCE:
        path = repo / rel
        rows.append(
            {
                "role": role,
                "path": rel,
                "present": path.is_file(),
            }
        )
    return rows


def load_intake_gate(repo: Path) -> dict[str, Any]:
    path = repo / "audit" / "evidence" / "customer-intake-gate.json"
    if not path.is_file():
        raise Kt3WithoutCustomerError(f"missing intake gate: {path}")
    return _load_json(path)


def _true_intake_gates(intake: Mapping[str, Any]) -> list[str]:
    gates = intake.get("gates")
    if not isinstance(gates, dict):
        raise Kt3WithoutCustomerError("intake gate file missing gates object")
    true_keys = [key for key in INTAKE_GATE_KEYS if gates.get(key) is True]
    return true_keys


def _typical_errors_pin(repo: Path) -> dict[str, Any]:
    path = repo / "samples" / "benchmarks" / "samolet-typical-errors-catalog.json"
    catalog = _load_json(path)
    patterns = catalog.get("patterns")
    count = len(patterns) if isinstance(patterns, list) else 0
    confirmed = catalog.get("customer_confirmed_patterns", 0)
    return {
        "pattern_count": count,
        "customer_confirmed_patterns": confirmed if isinstance(confirmed, int) else 0,
        "catalog_status": catalog.get("catalog_status"),
    }


def assemble_kt3_without_customer(
    repo: Path,
    *,
    generated_at: str,
    intake: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose the KT#3 pack that does not wait for a customer corpus."""

    evidence = inventory_required_evidence(repo)
    missing = [row["path"] for row in evidence if not row["present"]]
    gate = dict(intake) if intake is not None else load_intake_gate(repo)
    true_gates = _true_intake_gates(gate)
    freeze = _load_json(
        repo / "samples/benchmarks/rt001-preregistration-synthetic-freeze-2026-08-14.json"
    )
    pointer = _load_json(repo / "samples/ids/moexp/jurisdiction-profile-pointer.json")
    typical = _typical_errors_pin(repo)
    tracker = tracker_snapshot()
    volumes = assemble_rt_blocker_volumes(repo)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "kt3_without_customer",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": generated_at,
        "checkpoint": CHECKPOINT,
        "go_kind": GO_KIND,
        "customer_go": CUSTOMER_GO,
        "market_go": False,
        "deployment_go": False,
        "mik_stage": "доработка",
        "validation_effectiveness_started": False,
        "deployment_started": False,
        "plan_b_decision": PLAN_B_DECISION,
        "owner_decision_date": OWNER_DECISION_DATE,
        "program_fork_date": PROGRAM_FORK_DATE,
        "customer_files_expected": False,
        "waiting_for_customer": False,
        "nda_corpus_in_git": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "rt001_split": volumes["RT-001"],
        "rt002_split": volumes["RT-002"],
        "rt003_split": volumes["RT-003"],
        "volume_re_scope_date": volumes["volume_re_scope_date"],
        "demo_command": DEMO_COMMAND,
        "pack_command": PACK_COMMAND,
        "jury_command": JURY_PACK_COMMAND,
        "show_tracks": {
            "jury_laptop": [JURY_PACK_COMMAND, DEMO_COMMAND, PACK_COMMAND],
            "regulatory_leg": "AEROBIM_SIGNOFF_PROFILE=moscow_agr_2026",
            "owner_optional_nda": "local customer files are not in git; never RT-001 CLOSED",
        },
        "tz_mvp_demonstrable": list(TZ_MVP_DEMONSTRABLE),
        "tz_explicit_gaps": list(TZ_EXPLICIT_GAPS),
        "paper_objects": list(PAPER_OBJECTS),
        "typical_errors": typical,
        "tracker": tracker,
        "tracker_eight": tracker_eight_snapshot(),
        "mik_m2_m8": "VERIFY_WITH_OPERATOR",
        "evidence": evidence,
        "intake_status": gate.get("status"),
        "intake_true_gates": true_gates,
        "synthetic_freeze_closes_rt001": bool(freeze.get("closes_rt001")),
        "jurisdiction_samolet_alias": bool(pointer.get("samolet_alias")),
        "customer_pack_hash": pointer.get("customer_pack_hash"),
    }
    require_honest_kt3_payload(payload, missing=missing)
    return payload


def require_honest_kt3_payload(
    payload: Mapping[str, Any],
    *,
    missing: list[str] | None = None,
) -> None:
    errors: list[str] = []
    if missing:
        errors.append("missing evidence: " + ", ".join(missing))
    if payload.get("checkpoint") != CHECKPOINT:
        errors.append(f"checkpoint={payload.get('checkpoint')!r}")
    if payload.get("go_kind") != GO_KIND:
        errors.append(f"go_kind={payload.get('go_kind')!r}")
    if payload.get("customer_go") is not False:
        errors.append("customer_go must stay false")
    if payload.get("plan_b_decision") != PLAN_B_DECISION:
        errors.append(f"plan_b_decision={payload.get('plan_b_decision')!r}")
    if payload.get("customer_files_expected") is not False:
        errors.append("customer_files_expected must be false")
    if payload.get("waiting_for_customer") is not False:
        errors.append("waiting_for_customer must be false")
    if payload.get("closes_rt001") is not False:
        errors.append("closes_rt001 must stay false")
    if payload.get("closes_rt002") is not False:
        errors.append("closes_rt002 must stay false")
    if payload.get("closes_rt003") is not False:
        errors.append("closes_rt003 must stay false")
    if payload.get("validation_effectiveness_started") is not False:
        errors.append("validation_effectiveness_started must stay false")
    if payload.get("claim_level") != CLAIM_LEVEL:
        errors.append(f"claim_level={payload.get('claim_level')!r}")
    true_gates = payload.get("intake_true_gates")
    if true_gates:
        errors.append("intake gates still true: " + ", ".join(str(g) for g in true_gates))
    if payload.get("synthetic_freeze_closes_rt001") is True:
        errors.append("synthetic freeze must not close RT-001")
    if payload.get("jurisdiction_samolet_alias") is True:
        errors.append("jurisdiction pointer must not alias Samolet")
    if payload.get("customer_pack_hash") not in (None, "", False):
        errors.append("customer_pack_hash must stay null without customer files")
    if payload.get("nda_corpus_in_git") is not False:
        errors.append("nda_corpus_in_git must stay false")
    split = payload.get("rt002_split")
    if not isinstance(split, dict) or split.get("b_corporate") != "OPEN":
        errors.append("rt002_split.b_corporate must stay OPEN")
    if not isinstance(split, dict) or split.get("c_corporate_signed") != "OPEN":
        errors.append("rt002_split.c_corporate_signed must stay OPEN")
    if not isinstance(split, dict) or split.get("a_regulatory") != "CLOSED":
        errors.append("rt002_split.a_regulatory must stay CLOSED")
    if not isinstance(split, dict) or split.get("b_eir_carrier") != "CLOSED":
        errors.append("rt002_split.b_eir_carrier must stay CLOSED")
    if isinstance(split, dict) and split.get("undifferentiated_closed_forbidden") is not True:
        errors.append("must forbid undifferentiated RT-002 CLOSED")
    rt001 = payload.get("rt001_split")
    if not isinstance(rt001, dict) or rt001.get("b_criterion_dual_rater") != "OPEN":
        errors.append("rt001_split.b_criterion_dual_rater must stay OPEN")
    if not isinstance(rt001, dict) or rt001.get("b_protocol_rehearsal") != "CLOSED":
        errors.append("rt001_split.b_protocol_rehearsal must stay CLOSED")
    if not isinstance(rt001, dict) or rt001.get("a_content_pairing") != "CLOSED":
        errors.append("rt001_split.a_content_pairing must stay CLOSED")
    rt003 = payload.get("rt003_split")
    if not isinstance(rt003, dict) or rt003.get("b_mep_system_clash") != "OPEN":
        errors.append("rt003_split.b_mep_system_clash must stay OPEN")
    if not isinstance(rt003, dict) or rt003.get("b_navis_federation_carrier") != "CLOSED":
        errors.append("rt003_split.b_navis_federation_carrier must stay CLOSED")
    if not isinstance(rt003, dict) or rt003.get("b_ifc_system_graph_rehearsal") != "CLOSED":
        errors.append("rt003_split.b_ifc_system_graph_rehearsal must stay CLOSED")
    if not isinstance(rt003, dict) or rt003.get("a_federated_geometric_rehearsal") != "CLOSED":
        errors.append("rt003_split.a_federated_geometric_rehearsal must stay CLOSED")
    gaps = payload.get("tz_explicit_gaps")
    if not isinstance(gaps, list) or not any("90%" in str(item) for item in gaps):
        errors.append("tz_explicit_gaps must keep publishable >90% as a gap")
    papers = payload.get("paper_objects")
    if not isinstance(papers, list) or len(papers) != 4:
        errors.append("paper_objects must stay the four unmixed Samolet papers")
    typical = payload.get("typical_errors")
    if not isinstance(typical, dict):
        errors.append("typical_errors pin missing")
    else:
        if int(typical.get("customer_confirmed_patterns") or 0) != 0:
            errors.append("customer_confirmed_patterns must stay 0")
        if int(typical.get("pattern_count") or 0) < 20:
            errors.append("synthetic typical-error catalog must stay ≥20")
    tracker = payload.get("tracker")
    if not isinstance(tracker, dict) or tracker.get("scheduled_demos_in_git") is not False:
        errors.append("tracker must not publish scheduled-demo counts in git")
    eight = payload.get("tracker_eight")
    if not isinstance(eight, dict) or eight.get("item_count") != 8:
        errors.append("tracker_eight must have 8 items")
    if isinstance(eight, dict) and eight.get("auth_bff_status") != "NOT_IMPLEMENTED":
        errors.append("tracker_eight auth_bff must stay NOT_IMPLEMENTED")
    if isinstance(eight, dict) and eight.get("finding_volume_is_accuracy") is not False:
        errors.append("finding volume must not be labeled accuracy")
    if payload.get("mik_m2_m8") != "VERIFY_WITH_OPERATOR":
        errors.append("mik_m2_m8 must stay VERIFY_WITH_OPERATOR")
    if errors:
        raise Kt3WithoutCustomerError("; ".join(errors))


def render_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "<!-- claims-lint: allow-file reason="
        '"KT#3 re-scope without customer files; RT blockers stay OPEN; '
        'forbidden phrases as non-claims" -->',
        "---",
        'title: "KT#3 without Samolet files — owner re-scope"',
        f'date: "{OWNER_DECISION_DATE}"',
        f"claim_level: {payload['claim_level']}",
        f"claim_boundary: {json.dumps(payload['claim_boundary'], ensure_ascii=False)}",
        "checkpoint: GO",
        "go_kind: regulatory_measurement_mvp",
        "customer_go: false",
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "customer_files_expected: false",
        "nda_corpus_in_git: false",
        f"plan_b_decision: {payload['plan_b_decision']}",
        "---",
        "",
        "# КТ#3 без файлов Самолёта в git",
        "",
        "Файлов заказчика **в git нет и не ожидается**. Календарная развилка программы "
        f"**{PROGRAM_FORK_DATE}** не отменяется и не ждётся. Локальный диск владельца "
        "не входит в этот пакет и не закрывает RT-001.",
        "",
        f"- Checkpoint: **{payload['checkpoint']}** (`{payload.get('go_kind')}`)",
        f"- customer_go: **{json.dumps(bool(payload.get('customer_go')))}**",
        f"- Стадия МИК: **{payload['mik_stage']}**",
        "- Валидация эффективности: **не начата**",
        f"- nda_corpus_in_git: **{json.dumps(bool(payload.get('nda_corpus_in_git')))}**",
        f"- closes_rt001: **{json.dumps(bool(payload['closes_rt001']))}**",
        f"- closes_rt002: **{json.dumps(bool(payload['closes_rt002']))}** "
        "(не произносить CLOSED без split a/b)",
        f"- closes_rt003: **{json.dumps(bool(payload['closes_rt003']))}**",
    ]
    rt001 = payload.get("rt001_split") or {}
    rt002 = payload.get("rt002_split") or {}
    rt003 = payload.get("rt003_split") or {}
    lines.extend(
        [
            f"- RT-001 split: content pairing **{rt001.get('a_content_pairing')}**; "
            f"protocol rehearsal **{rt001.get('b_protocol_rehearsal')}**; "
            f"dual-rater **{rt001.get('b_criterion_dual_rater')}**",
            f"- RT-002 split: regulatory **{rt002.get('a_regulatory')}**; "
            f"EIR carrier **{rt002.get('b_eir_carrier')}**; "
            f"signed corporate **{rt002.get('c_corporate_signed')}**",
            f"- RT-003 split: planted geometric "
            f"**{rt003.get('a_federated_geometric_rehearsal')}**; "
            f"NWD carrier **{rt003.get('b_navis_federation_carrier')}**; "
            f"IfcSystem rehearsal **{rt003.get('b_ifc_system_graph_rehearsal')}**; "
            f"mep_system_clash **{rt003.get('b_mep_system_clash')}**",
            f"- Показ (одна команда): `{payload.get('jury_command') or payload['demo_command']}`",
            f"- Gate (если жюри просит отдельно): `{payload['demo_command']}`",
            f"- Пакет без заказчика: `{payload['pack_command']}`",
            "- Карточка речи: `docs/demo/KT3_JURY_FAQ_2026_08_25.md`",
            "- Сценарий оператора: `docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md`",
            "- Трекер (6 задач): `docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md`",
            "",
            str(payload["claim_boundary"]),
            "",
            "| Роль | Файл | Есть |",
            "|---|---|---|",
        ]
    )
    for row in payload.get("evidence") or []:
        if not isinstance(row, dict):
            continue
        present = "yes" if row.get("present") else "NO"
        lines.append(f"| {row.get('role')} | `{row.get('path')}` | {present} |")
    lines.append("")
    return "\n".join(lines)
