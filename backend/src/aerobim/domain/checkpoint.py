"""Product checkpoint SSOT.

Owner re-scope 2026-09-04: Checkpoint ``GO`` is the regulatory-measurement MVP
(public examination IDS, fixture gold, planted clash, HVAC IfcSystem rehearsal,
channel EIR/NWD carriers). That is not customer sign-off.

``customer_go`` / ``market_go`` / ``deployment_go`` stay false.
Undifferentiated ``closes_rt001`` / ``closes_rt002`` / ``closes_rt003`` stay
false. Simulated raters are not humans. City AGR NPA is not a named
appointing-party signed IDS. Signed OOS does not close RT-003.
``PrecisionClaim.publishable`` stays false. MEP delivered is not claimed.
CDE T2 stays ``NOT_VERIFIED``.

KT#2 frozen handoff pins (August 2026) remain historical ``NO_GO`` snapshots.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

CHECKPOINT: Final = "GO"
GO_KIND: Final = "regulatory_measurement_mvp"
GO_RE_SCOPE_DATE: Final = "2026-09-04"
CUSTOMER_GO: Final = False
MARKET_GO: Final = False
DEPLOYMENT_GO: Final = False
PRECISION_PUBLISHABLE: Final = False
MEP_DELIVERED: Final = False
CDE_IMPORT: Final = "NOT_VERIFIED"

CLAIM_BOUNDARY: Final = (
    "Checkpoint GO is the regulatory-measurement MVP: public examination IDS "
    "(MOEXP/CGE/AGR), fixture gold, planted geometric clash, HVAC IfcSystem "
    "graph rehearsal, and git-safe channel carriers (EIR v4 text, NWD "
    "federations). customer_go stays false. Not two human raters. Not a named "
    "appointing-party signed IDS. Not mep_system_clash=OK. Not CDE import. "
    "Not product accuracy. Not customer SLA. closes_rt001/002/003 stay false."
)

CHECKPOINT_SPEECH: Final = (
    f"Checkpoint {CHECKPOINT} ({GO_KIND}). customer_go stays false. "
    "Not product accuracy. Not customer SLA. Not MEP delivered. Not CDE-ready. "
    "closes_rt001/002/003 stay false."
)

SPEECH_FORMULA_RU: Final = (
    "Мы на стадии доработки контура заказчика. Одна команда показывает находку "
    "с доказательствами на учебном комплекте. Валидация эффективности и внедрение "
    "у назначающей стороны ещё не начались. Checkpoint `GO` — регуляторно-измерительный "
    "MVP. `customer_go` остаётся false, пока нет независимого размеченного корпуса, "
    "двух разметчиков, подписанного профиля назначающей стороны и подтверждения "
    "импорта в СОД."
)

SPEECH_FORMULA_EN: Final = (
    "We are in *refinement* on the customer contour. One command shows a fail-closed "
    "finding on a fixture. Effectiveness validation and deployment have not started. "
    "Checkpoint `GO` is the regulatory-measurement MVP. `customer_go` stays false until "
    "an independent labeled pack, two raters, a signed appointing-party profile, and "
    "CDE proof."
)

SPEECH_FORMULA_MARKERS: Final[tuple[str, ...]] = (
    "Мы на стадии доработки контура заказчика",
    "Одна команда показывает находку с доказательствами на учебном комплекте",
    "Валидация эффективности и внедрение у назначающей стороны ещё не начались",
    "Checkpoint `GO` — регуляторно-измерительный MVP",
    "`customer_go` остаётся false, пока нет независимого размеченного корпуса",
)


class CheckpointHonestyError(ValueError):
    """Payload claimed GO without the regulatory-MVP honesty fields."""


def checkpoint_fields() -> dict[str, Any]:
    """Standard checkpoint block for JSON snapshots."""

    return {
        "checkpoint": CHECKPOINT,
        "go_kind": GO_KIND,
        "go_re_scope_date": GO_RE_SCOPE_DATE,
        "customer_go": CUSTOMER_GO,
        "market_go": MARKET_GO,
        "deployment_go": DEPLOYMENT_GO,
    }


def require_honest_checkpoint(payload: Mapping[str, Any]) -> None:
    """Live snapshots must be GO + regulatory kind, with customer_go false."""

    errors: list[str] = []
    if payload.get("checkpoint") != CHECKPOINT:
        errors.append(f"checkpoint={payload.get('checkpoint')!r} (want {CHECKPOINT})")
    if payload.get("go_kind") not in (None, GO_KIND):
        errors.append(f"go_kind={payload.get('go_kind')!r}")
    if payload.get("customer_go") is not False:
        errors.append("customer_go must stay false")
    if payload.get("market_go") is True:
        errors.append("market_go must stay false")
    if payload.get("deployment_go") is True:
        errors.append("deployment_go must stay false")
    if errors:
        raise CheckpointHonestyError("; ".join(errors))


__all__ = [
    "CDE_IMPORT",
    "CHECKPOINT",
    "CHECKPOINT_SPEECH",
    "CLAIM_BOUNDARY",
    "CUSTOMER_GO",
    "DEPLOYMENT_GO",
    "GO_KIND",
    "GO_RE_SCOPE_DATE",
    "MARKET_GO",
    "MEP_DELIVERED",
    "PRECISION_PUBLISHABLE",
    "SPEECH_FORMULA_EN",
    "SPEECH_FORMULA_MARKERS",
    "SPEECH_FORMULA_RU",
    "CheckpointHonestyError",
    "checkpoint_fields",
    "require_honest_checkpoint",
]
