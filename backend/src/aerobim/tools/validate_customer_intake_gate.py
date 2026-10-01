"""CLI entry — intake gate logic lives in application.services.customer_intake_gate."""

from __future__ import annotations

from aerobim.application.services.customer_intake_gate import (
    INTAKE_GATE_KEYS,
    default_gate_path,
    main,
    validate_customer_intake_gate,
)

__all__ = [
    "INTAKE_GATE_KEYS",
    "default_gate_path",
    "main",
    "validate_customer_intake_gate",
]


if __name__ == "__main__":
    main()
