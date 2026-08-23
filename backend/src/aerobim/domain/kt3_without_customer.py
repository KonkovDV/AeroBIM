"""KT#3 without Samolet files: re-scope is the product decision, not a wait state.

Does not close RT-001/002/003. Does not publish product accuracy.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from aerobim.application.services.customer_intake_gate import INTAKE_GATE_KEYS

PLAN_B_DECISION: Final = "re-scope"
OWNER_DECISION_DATE: Final = "2026-08-23"
PROGRAM_FORK_DATE: Final = "2026-09-15"
CLAIM_LEVEL: Final = "fixture_and_proxy_only"
DEMO_COMMAND: Final = "python -m aerobim.tools.run_demo_ifc_acceptance_gate"
PACK_COMMAND: Final = "python -m aerobim.tools.run_kt3_without_customer"

CLAIM_BOUNDARY: Final = (
    "Owner re-scope 2026-08-23: customer files are not expected. "
    "KT#3 is the live fixture gate plus public/synthetic proxies. "
    "Not product accuracy. Not customer SLA. Not MEP delivered. "
    "Not CDE-ready. Checkpoint NO_GO. closes_rt001/002/003 stay false."
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
    ("rt_without_samolet", "docs/datasets/RT001_002_003_WITHOUT_SAMOLET_2026_08_14.md"),
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

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "artifact_type": "kt3_without_customer",
        "claim_level": CLAIM_LEVEL,
        "claim_boundary": CLAIM_BOUNDARY,
        "generated_at": generated_at,
        "checkpoint": "NO_GO",
        "mik_stage": "доработка",
        "validation_effectiveness_started": False,
        "deployment_started": False,
        "plan_b_decision": PLAN_B_DECISION,
        "owner_decision_date": OWNER_DECISION_DATE,
        "program_fork_date": PROGRAM_FORK_DATE,
        "customer_files_expected": False,
        "waiting_for_customer": False,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "demo_command": DEMO_COMMAND,
        "pack_command": PACK_COMMAND,
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
    if payload.get("checkpoint") != "NO_GO":
        errors.append(f"checkpoint={payload.get('checkpoint')!r}")
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
        "checkpoint: NO_GO",
        "closes_rt001: false",
        "closes_rt002: false",
        "closes_rt003: false",
        "customer_files_expected: false",
        f"plan_b_decision: {payload['plan_b_decision']}",
        "---",
        "",
        "# КТ#3 без файлов Самолёта",
        "",
        "Файлов заказчика не будет. Решение владельца **re-scope** "
        f"({OWNER_DECISION_DATE}). Календарная развилка программы "
        f"**{PROGRAM_FORK_DATE}** не отменяется и не ждётся.",
        "",
        f"- Checkpoint: **{payload['checkpoint']}**",
        f"- Стадия МИК: **{payload['mik_stage']}**",
        "- Валидация эффективности: **не начата**",
        f"- closes_rt001: **{json.dumps(bool(payload['closes_rt001']))}**",
        f"- closes_rt002: **{json.dumps(bool(payload['closes_rt002']))}**",
        f"- closes_rt003: **{json.dumps(bool(payload['closes_rt003']))}**",
        f"- Показ: `{payload['demo_command']}`",
        f"- Пакет без заказчика: `{payload['pack_command']}`",
        "",
        str(payload["claim_boundary"]),
        "",
        "| Роль | Файл | Есть |",
        "|---|---|---|",
    ]
    for row in payload.get("evidence") or []:
        if not isinstance(row, dict):
            continue
        present = "yes" if row.get("present") else "NO"
        lines.append(f"| {row.get('role')} | `{row.get('path')}` | {present} |")
    lines.append("")
    return "\n".join(lines)
