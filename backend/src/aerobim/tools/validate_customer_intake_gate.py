"""Validate customer-intake-gate.json — fail closed if gates flip without evidence."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_GATE_KEYS = (
    "nda_signed",
    "scope_memo_signed",
    "customer_package_in_samples_customer",
    "customer_approved_norm_pack_with_approval_ref",
    "ids_or_property_table_present",
    "dual_human_adjudicators_named",
    "cohens_kappa_or_krippendorff_alpha_reported",
    "confusion_matrix_reported",
    "zero_unresolved_labels",
    "precision_claim_publishable",
    "cde_bcf_import_evidence",
    "customer_sla_pack_measured",
    "mep_federated_scope",
)

_FORBIDDEN_RULES = (
    "llm_assist_counts_as_adjudicator",
    "synthetic_f1_is_product_accuracy",
    "fixture_sla_is_customer_sla",
    "customer_approved_without_approval_ref",
)


def validate_customer_intake_gate(path: Path) -> dict[str, Any]:
    """Return a validation report; ``ok`` is True only when policy holds."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    if payload.get("artifact_type") != "customer_intake_gate":
        errors.append("artifact_type must be customer_intake_gate")

    gates = payload.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}

    rules = payload.get("rules")
    if not isinstance(rules, dict):
        errors.append("rules must be an object")
        rules = {}

    for key in _GATE_KEYS:
        if key not in gates:
            errors.append(f"missing gate: {key}")
        elif not isinstance(gates[key], bool):
            errors.append(f"gate {key} must be boolean")

    for key in _FORBIDDEN_RULES:
        if rules.get(key) is True:
            errors.append(f"forbidden rule must stay false: {key}")

    evidence = payload.get("evidence")
    if evidence is not None and not isinstance(evidence, dict):
        errors.append("evidence must be an object when present")
        evidence = {}
    if not isinstance(evidence, dict):
        evidence = {}

    true_gates = [key for key in _GATE_KEYS if gates.get(key) is True]
    status = str(payload.get("status") or "")
    claim_level = str(payload.get("claim_level") or "")

    if status == "BLOCKED_NO_CUSTOMER_DATA" and true_gates:
        errors.append(
            "status BLOCKED_NO_CUSTOMER_DATA forbids true gates: " + ", ".join(true_gates)
        )

    if claim_level == "not_ready" and true_gates:
        warnings.append("claim_level=not_ready while some gates are true — verify evidence refs")

    for key in true_gates:
        ref = evidence.get(key)
        if not ref:
            errors.append(f"gate {key}=true requires evidence[{key}] path or digest")
        elif isinstance(ref, str):
            ref_path = Path(ref)
            if not ref_path.is_file():
                # Allow repo-relative paths from CWD or gate parent.
                alt = path.parent / ref
                if not alt.is_file() and not Path.cwd().joinpath(ref).is_file():
                    errors.append(f"evidence for {key} not found: {ref}")

    if gates.get("precision_claim_publishable") is True:
        for required in (
            "cohens_kappa_or_krippendorff_alpha_reported",
            "confusion_matrix_reported",
            "dual_human_adjudicators_named",
            "zero_unresolved_labels",
        ):
            if gates.get(required) is not True:
                errors.append(f"precision_claim_publishable=true requires {required}=true")
        for required_ev in (
            "cohens_kappa_or_krippendorff_alpha_reported",
            "precision_claim_publishable",
        ):
            if not evidence.get(required_ev):
                errors.append(f"precision_claim_publishable=true requires evidence[{required_ev}]")

    ok = not errors
    return {
        "artifact_type": "customer_intake_gate_validation",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source": str(path.as_posix()),
        "ok": ok,
        "true_gates": true_gates,
        "errors": errors,
        "warnings": warnings,
        "checkpoint_hint": "NO_GO" if not ok or true_gates == [] else "REVIEW",
        "notes": [
            "Default AeroBIM posture: all gates false → NO_GO until customer evidence",
            "Never set precision_claim_publishable without κ/α + confusion + dual humans",
        ],
    }


def default_gate_path() -> Path:
    """Resolve audit/evidence/customer-intake-gate.json from repo root."""

    return Path(__file__).resolve().parents[4] / "audit" / "evidence" / "customer-intake-gate.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate customer intake gate JSON")
    parser.add_argument(
        "--gate",
        type=Path,
        default=None,
        help="Path to customer-intake-gate.json (default: repo audit/evidence)",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    path = args.gate or default_gate_path()
    if not path.is_file():
        raise SystemExit(f"gate file not found: {path}")

    report = validate_customer_intake_gate(path)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(args.output)
    else:
        print(serialized)

    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
