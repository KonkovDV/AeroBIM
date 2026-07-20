"""Validate customer-intake-gate.json — fail closed if gates flip without evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.security.path_jail import PathJailError, resolve_storage_path

INTAKE_GATE_KEYS = (
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
_GATE_KEYS = INTAKE_GATE_KEYS

_FORBIDDEN_RULES = (
    "llm_assist_counts_as_adjudicator",
    "synthetic_f1_is_product_accuracy",
    "fixture_sla_is_customer_sla",
    "customer_approved_without_approval_ref",
)

_ALLOWED_EVIDENCE_MARKERS = (
    "/audit/evidence/",
    "/samples/customer/",
    "/docs/evidence/",
)
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _path_allowlisted(resolved: Path) -> bool:
    lowered = resolved.as_posix().lower()
    return any(marker in lowered for marker in _ALLOWED_EVIDENCE_MARKERS)


def _resolve_evidence_path(ref: str, gate_path: Path) -> Path | None:
    candidates = [
        Path(ref),
        gate_path.parent / ref,
        Path.cwd() / ref,
        _repo_root() / ref,
    ]
    # If gate lives under …/audit/evidence/, also try repo-relative from parents[2].
    if gate_path.parent.name == "evidence" and gate_path.parent.parent.name == "audit":
        candidates.append(gate_path.parents[2] / ref)
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def _validate_evidence_ref(key: str, ref: Any, gate_path: Path) -> list[str]:
    """RT-INTAKE-001: true gates require {path, sha256} under allowlisted roots."""

    errors: list[str] = []
    if isinstance(ref, str):
        errors.append(
            f"evidence[{key}] must be object {{path, sha256}} when gate is true "
            "(string paths are rejected)"
        )
        return errors
    if not isinstance(ref, dict):
        errors.append(f"evidence[{key}] must be object {{path, sha256}}")
        return errors
    path_value = ref.get("path")
    digest = ref.get("sha256")
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"evidence[{key}].path must be a non-empty string")
        return errors
    if not isinstance(digest, str) or not _SHA256_RE.match(digest):
        errors.append(f"evidence[{key}].sha256 must be 64 hex chars")
        return errors
    resolved = _resolve_evidence_path(path_value.strip(), gate_path)
    if resolved is None:
        errors.append(f"evidence for {key} not found: {path_value}")
        return errors
    if not _path_allowlisted(resolved):
        errors.append(
            f"evidence[{key}] path not under audit/evidence, samples/customer, "
            f"or docs/evidence: {resolved.as_posix()}"
        )
        return errors
    if resolved.stat().st_size <= 0:
        errors.append(f"evidence[{key}] file is empty: {resolved.as_posix()}")
        return errors
    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
    if actual.lower() != digest.lower():
        errors.append(f"evidence[{key}] sha256 mismatch: expected {digest.lower()}, got {actual}")
    return errors


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
            errors.append(f"gate {key}=true requires evidence[{key}] {{path, sha256}}")
        else:
            errors.extend(_validate_evidence_ref(key, ref, path))

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
        "schema_version": "1.1.0",
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
            "True-gate evidence requires {path, sha256} under allowlisted roots (RT-INTAKE-001)",
        ],
    }


def default_gate_path() -> Path:
    """Resolve audit/evidence/customer-intake-gate.json from repo root."""

    return _repo_root() / "audit" / "evidence" / "customer-intake-gate.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate customer intake gate JSON")
    parser.add_argument(
        "--gate",
        type=Path,
        default=None,
        help="Path to customer-intake-gate.json (default: repo audit/evidence)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Storage-relative path under repo audit/ (RT-CLI-001 jail)",
    )
    args = parser.parse_args()
    path = args.gate or default_gate_path()
    if not path.is_file():
        raise SystemExit(f"gate file not found: {path}")

    report = validate_customer_intake_gate(path)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        audit_root = _repo_root() / "audit"
        rel = args.output
        if rel.is_absolute():
            try:
                rel = Path(rel).resolve().relative_to(audit_root.resolve())
            except ValueError as exc:
                raise SystemExit(f"output must be under repo audit/: {args.output}") from exc
        try:
            out_path = resolve_storage_path(rel.as_posix(), base=audit_root)
        except PathJailError as exc:
            raise SystemExit(f"output path jail: {exc}") from exc
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(out_path)
    else:
        print(serialized)

    if not report["ok"]:
        raise SystemExit(2)
    if report["true_gates"] == []:
        print("checkpoint_hint=NO_GO (all gates false)", file=sys.stderr)


if __name__ == "__main__":
    main()
