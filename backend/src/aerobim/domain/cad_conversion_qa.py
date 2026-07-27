"""Conversion-loss QA for DWG→derived substitutes (gap analysis §1.4).

Deterministic diff of the *agreed* expected sheet/layer inventory against what
the external converter actually produced. Mirrors the round-trip-fidelity
posture of CAD data-exchange conformance testing (ISO 10303 / bSI software
certification): a conversion is only as good as the verified content diff.
The QA verdict feeds the derived route fail-closed: ``failed`` rejects the
substitute; ``warning`` keeps the route but surfaces the loss to the expert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ConversionQaStatus = Literal["ok", "warning", "failed"]

_QA_SECTION_KEY = "conversion_qa"


@dataclass(frozen=True)
class ConversionQaPolicy:
    """Escalation thresholds agreed with the customer (defaults are strict)."""

    max_layer_loss_ratio: float = 0.0
    """Layer-loss share above which the conversion fails (0.0 = any loss fails)."""
    missing_sheet_is_failure: bool = True
    """A missing expected sheet defaults to failure — sheets carry findings."""


@dataclass(frozen=True)
class ConversionQaReport:
    """Loss report for one registered conversion pair."""

    status: ConversionQaStatus
    missing_sheets: tuple[str, ...] = ()
    missing_layers: tuple[str, ...] = ()
    extra_layers: tuple[str, ...] = ()
    layer_loss_ratio: float = 0.0
    reasons: tuple[str, ...] = field(default=())


def _normalized(names: tuple[str, ...]) -> dict[str, str]:
    """Case-insensitive matching while preserving the declared spelling."""

    return {name.strip().lower(): name.strip() for name in names if name.strip()}


def evaluate_conversion_loss(
    *,
    expected_sheets: tuple[str, ...],
    expected_layers: tuple[str, ...],
    observed_sheets: tuple[str, ...],
    observed_layers: tuple[str, ...],
    policy: ConversionQaPolicy | None = None,
) -> ConversionQaReport:
    """Diff expected vs observed inventories; verdict per the agreed policy.

    ``layer_loss_ratio`` = missing / expected (0 when nothing was expected).
    Extra layers are reported but never escalate — only losses do.
    """

    active = policy or ConversionQaPolicy()
    expected_sheet_map = _normalized(expected_sheets)
    expected_layer_map = _normalized(expected_layers)
    observed_sheet_keys = set(_normalized(observed_sheets))
    observed_layer_map = _normalized(observed_layers)

    missing_sheets = tuple(
        expected_sheet_map[key]
        for key in sorted(expected_sheet_map)
        if key not in observed_sheet_keys
    )
    missing_layers = tuple(
        expected_layer_map[key]
        for key in sorted(expected_layer_map)
        if key not in observed_layer_map
    )
    extra_layers = tuple(
        observed_layer_map[key]
        for key in sorted(observed_layer_map)
        if key not in expected_layer_map
    )
    layer_loss_ratio = len(missing_layers) / len(expected_layer_map) if expected_layer_map else 0.0

    reasons: list[str] = []
    status: ConversionQaStatus = "ok"
    if missing_sheets:
        reasons.append(f"missing expected sheets: {', '.join(missing_sheets)}")
        status = "failed" if active.missing_sheet_is_failure else "warning"
    if missing_layers:
        reasons.append(
            f"layer loss {layer_loss_ratio:.2%} "
            f"({len(missing_layers)}/{len(expected_layer_map)}): " + ", ".join(missing_layers)
        )
        if layer_loss_ratio > active.max_layer_loss_ratio:
            status = "failed"
        elif status != "failed":
            status = "warning"
    if extra_layers and status == "ok":
        # Informational only — renamed/added layers deserve expert attention.
        reasons.append(f"extra layers in derived file: {', '.join(extra_layers)}")

    return ConversionQaReport(
        status=status,
        missing_sheets=missing_sheets,
        missing_layers=missing_layers,
        extra_layers=extra_layers,
        layer_loss_ratio=layer_loss_ratio,
        reasons=tuple(reasons),
    )


def conversion_qa_section_payload(
    *,
    expected_sheets: tuple[str, ...],
    expected_layers: tuple[str, ...],
    observed_sheets: tuple[str, ...],
    observed_layers: tuple[str, ...],
    policy: ConversionQaPolicy,
) -> dict[str, object]:
    """Sidecar ``conversion_qa`` section (inputs, not the verdict — always recomputed)."""

    return {
        "expected_sheets": list(expected_sheets),
        "expected_layers": list(expected_layers),
        "observed_sheets": list(observed_sheets),
        "observed_layers": list(observed_layers),
        "max_layer_loss_ratio": policy.max_layer_loss_ratio,
        "missing_sheet_is_failure": policy.missing_sheet_is_failure,
    }


def _str_tuple(value: object, key: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array of strings")
    return tuple(str(item) for item in value)


def evaluate_conversion_qa_section(payload: dict[str, object]) -> ConversionQaReport | None:
    """Recompute the QA verdict from a sidecar payload; malformed section fails closed.

    Returns ``None`` when no ``conversion_qa`` section is declared (QA optional
    until the customer converter and inventories are agreed). The verdict is
    never read from the sidecar — only inputs are, so a hand-edited "status"
    cannot whitewash a lossy conversion.
    """

    raw = payload.get(_QA_SECTION_KEY)
    if raw is None:
        return None
    try:
        if not isinstance(raw, dict):
            raise ValueError(f"{_QA_SECTION_KEY} must be an object")
        policy = ConversionQaPolicy(
            max_layer_loss_ratio=float(raw.get("max_layer_loss_ratio", 0.0)),
            missing_sheet_is_failure=bool(raw.get("missing_sheet_is_failure", True)),
        )
        if not 0.0 <= policy.max_layer_loss_ratio <= 1.0:
            raise ValueError("max_layer_loss_ratio must be within [0, 1]")
        return evaluate_conversion_loss(
            expected_sheets=_str_tuple(raw.get("expected_sheets"), "expected_sheets"),
            expected_layers=_str_tuple(raw.get("expected_layers"), "expected_layers"),
            observed_sheets=_str_tuple(raw.get("observed_sheets"), "observed_sheets"),
            observed_layers=_str_tuple(raw.get("observed_layers"), "observed_layers"),
            policy=policy,
        )
    except (TypeError, ValueError) as exc:
        return ConversionQaReport(
            status="failed",
            reasons=(f"conversion_qa section malformed: {exc}",),
        )


__all__ = [
    "ConversionQaPolicy",
    "ConversionQaReport",
    "ConversionQaStatus",
    "conversion_qa_section_payload",
    "evaluate_conversion_loss",
    "evaluate_conversion_qa_section",
]
