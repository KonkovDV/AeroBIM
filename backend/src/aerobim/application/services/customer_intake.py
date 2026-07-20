"""Customer intake gate evaluation for pilot fail-closed sign-off."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aerobim.tools.validate_customer_intake_gate import (
    INTAKE_GATE_KEYS,
    default_gate_path,
    validate_customer_intake_gate,
)


@dataclass(frozen=True)
class IntakeResult:
    """Result of evaluating the customer intake manifest for pilot readiness."""

    ok: bool
    status: str
    reasons: list[str]
    true_gates: list[str]


class CustomerIntakeGate:
    """Evaluate ``customer-intake-gate.json`` for samolet_pilot fail-closed."""

    @staticmethod
    def evaluate(path: Path) -> IntakeResult:
        if not path.is_file():
            return IntakeResult(
                ok=False,
                status="MISSING_GATE_FILE",
                reasons=[f"customer intake gate file not found: {path.as_posix()}"],
                true_gates=[],
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return IntakeResult(
                ok=False,
                status="UNREADABLE_GATE_FILE",
                reasons=[f"customer intake gate unreadable: {exc}"],
                true_gates=[],
            )

        if not isinstance(payload, dict):
            return IntakeResult(
                ok=False,
                status="INVALID_GATE_FILE",
                reasons=["customer intake gate payload must be a JSON object"],
                true_gates=[],
            )

        report = validate_customer_intake_gate(path)
        status = str(payload.get("status") or "")
        true_gates = [str(item) for item in report.get("true_gates") or []]
        reasons: list[str] = [str(err) for err in report.get("errors") or []]

        raw_gates = payload.get("gates")
        gates: dict[str, object] = raw_gates if isinstance(raw_gates, dict) else {}
        false_gates = [key for key in INTAKE_GATE_KEYS if gates.get(key) is not True]
        if false_gates:
            reasons.append("required intake gates false: " + ", ".join(false_gates))

        status_upper = status.upper()
        if status_upper.startswith("BLOCKED") or status_upper in {
            "BLOCKED_NO_CUSTOMER_DATA",
            "NO_GO",
        }:
            reasons.append(f"intake status is blocked: {status or 'unknown'}")

        # Deduplicate while preserving order.
        seen: set[str] = set()
        unique_reasons: list[str] = []
        for reason in reasons:
            if reason in seen:
                continue
            seen.add(reason)
            unique_reasons.append(reason)

        ok = (
            bool(report.get("ok"))
            and not false_gates
            and not status_upper.startswith("BLOCKED")
            and status_upper not in {"NO_GO"}
        )
        return IntakeResult(
            ok=ok,
            status=status or ("READY" if ok else "BLOCKED"),
            reasons=unique_reasons,
            true_gates=true_gates,
        )

    @staticmethod
    def default_path() -> Path:
        return default_gate_path()
