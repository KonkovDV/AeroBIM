"""Git-safe index of the 14.09 customer delivery: three packs + trial access.

Reports themselves stay in ``.local/``. GitHub is not a delivery channel.
No Samolet direct contact: organizers only. Deadline 14.09 is final.
Demo-seed is not a customer report. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO, PRECISION_PUBLISHABLE

CLAIM_BOUNDARY: Final = (
    "Index of three channel packs and a trial-access mode. "
    "Sole customer channel is organizers. No Samolet direct contact. "
    "Customer deadline 14.09 is final; a later call is not delivery. "
    "Not product accuracy. Not pack processed. Not a GitHub-hosted NDA tree. "
    "Demo-seed is not a customer report. Checkpoint GO; customer_go false."
)

SCHEMA_VERSION: Final = "1.1.0"
ARTIFACT_TYPE: Final = "customer_delivery_index"
DEADLINE: Final = "2026-09-14"
DELIVERY_CHANNEL: Final = "organizers_only"

PACK_SLOTS: Final[tuple[str, ...]] = ("pack_a", "pack_b", "pack_c")

PackStatus = Literal["not_run", "ready_local", "sent", "received"]
TrialMode = Literal[
    "unspecified",
    "on_prem_docker",
    "operator_https_timeboxed",
    "screen_share_only",
]

PACK_STATUSES: Final[frozenset[str]] = frozenset({"not_run", "ready_local", "sent", "received"})
TRIAL_MODES: Final[frozenset[str]] = frozenset(
    {"unspecified", "on_prem_docker", "operator_https_timeboxed", "screen_share_only"}
)
SELF_SERVE_MODES: Final[frozenset[str]] = frozenset({"on_prem_docker", "operator_https_timeboxed"})
REQUIRED_EXPORTS: Final[tuple[str, ...]] = ("html", "json", "pdf", "bcf")

_DEMO_MARKERS: Final[tuple[str, ...]] = (
    "seed-fixture",
    "demo-seed",
    "demo_seed",
)
_PUBLIC_HOST_MARKERS: Final[tuple[str, ...]] = (
    "github.com",
    "githubusercontent.com",
    "gitlab.com",
    "bitbucket.org",
)


class DeliveryIndexError(ValueError):
    """Operator-filled delivery index failed a fail-closed check."""


def _is_demo_seed_id(report_id: object) -> bool:
    text = str(report_id or "").strip().casefold()
    if not text:
        return False
    if text.replace("9", "") == "" and len(text) >= 8:
        return True
    return any(marker in text for marker in _DEMO_MARKERS)


def _url_is_public_host(url: object) -> bool:
    text = str(url or "").strip().casefold()
    return any(marker in text for marker in _PUBLIC_HOST_MARKERS)


def empty_pack_row(slot: str) -> dict[str, Any]:
    return {
        "slot": slot,
        "status": "not_run",
        "report_id": None,
        "export_kinds": list(REQUIRED_EXPORTS),
        "is_demo_seed": False,
        "link_channel": "organizers_not_github",
    }


def empty_delivery_index() -> dict[str, Any]:
    """Default index: three empty slots. Not a completed delivery."""

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "deadline": DEADLINE,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "precision_claim_publishable": PRECISION_PUBLISHABLE,
        "is_accuracy": False,
        "git_hosts_reports": False,
        "seed_fixture_on_trial": False,
        "samolet_direct_contact": False,
        "delivery_channel": DELIVERY_CHANNEL,
        "customer_deadline_is_final": True,
        "post_deadline_slot_is_not_delivery": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "packs": [empty_pack_row(slot) for slot in PACK_SLOTS],
        "trial": {
            "mode": "unspecified",
            "independent_test": False,
            "anonymous": False,
            "roles": ["expert", "viewer"],
            "https_required": True,
            "cloud_rejected": True,
        },
        "ready_for_deadline": False,
    }


def _normalize_pack(row: Mapping[str, Any], *, expected_slot: str) -> dict[str, Any]:
    slot = str(row.get("slot") or "").strip()
    if slot != expected_slot:
        raise DeliveryIndexError(f"expected slot {expected_slot!r}, got {slot!r}")
    status = str(row.get("status") or "not_run").strip()
    if status not in PACK_STATUSES:
        raise DeliveryIndexError(f"unknown pack status {status!r}")
    report_id = row.get("report_id")
    if report_id is not None:
        report_id = str(report_id).strip() or None
    if _is_demo_seed_id(report_id):
        raise DeliveryIndexError("demo-seed report_id cannot fill a customer pack slot")
    url = row.get("url") or row.get("href")
    if _url_is_public_host(url):
        raise DeliveryIndexError("public git host is not a delivery channel for pack reports")
    if status == "not_run" and report_id:
        raise DeliveryIndexError(f"{slot} status not_run cannot carry report_id")
    if status in {"ready_local", "sent", "received"} and not report_id:
        raise DeliveryIndexError(f"{slot} status {status} requires report_id")
    export_kinds = [
        str(kind).strip().casefold() for kind in (row.get("export_kinds") or REQUIRED_EXPORTS)
    ]
    if status in {"ready_local", "sent", "received"}:
        missing = [kind for kind in REQUIRED_EXPORTS if kind not in export_kinds]
        if missing:
            raise DeliveryIndexError(
                f"{slot} status {status} requires export kinds "
                f"{REQUIRED_EXPORTS}, missing {missing}"
            )
    return {
        "slot": slot,
        "status": status,
        "report_id": report_id,
        "export_kinds": list(export_kinds or REQUIRED_EXPORTS),
        "is_demo_seed": False,
        "link_channel": "organizers_not_github",
    }


def _normalize_trial(trial: object) -> dict[str, Any]:
    payload = dict(trial) if isinstance(trial, Mapping) else {}
    mode = str(payload.get("mode") or "unspecified").strip()
    if mode not in TRIAL_MODES:
        raise DeliveryIndexError(f"unknown trial mode {mode!r}")
    if payload.get("seed_fixture_on_trial") or payload.get("seed_fixture_enabled"):
        raise DeliveryIndexError("trial must not enable seed-fixture")
    anonymous = bool(payload.get("anonymous"))
    if anonymous:
        raise DeliveryIndexError("trial anonymous access is not allowed")
    independent = mode in SELF_SERVE_MODES
    if mode == "screen_share_only":
        independent = False
    return {
        "mode": mode,
        "independent_test": independent,
        "anonymous": False,
        "roles": list(payload.get("roles") or ["expert", "viewer"]),
        "https_required": True,
        "cloud_rejected": True,
    }


def validate_delivery_index(data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an operator-filled index. Does not invent report_ids."""

    packs_raw = data.get("packs")
    if not isinstance(packs_raw, Sequence) or len(packs_raw) != 3:
        raise DeliveryIndexError("delivery index requires exactly three pack rows")
    packs = [
        _normalize_pack(row, expected_slot=slot)
        for slot, row in zip(PACK_SLOTS, packs_raw, strict=True)
        if isinstance(row, Mapping)
    ]
    if len(packs) != 3:
        raise DeliveryIndexError("each pack row must be an object")
    trial = _normalize_trial(data.get("trial"))
    if data.get("samolet_direct_contact"):
        raise DeliveryIndexError("no Samolet direct contact; organizers are the sole channel")
    channel = str(data.get("delivery_channel") or DELIVERY_CHANNEL).strip()
    if channel != DELIVERY_CHANNEL:
        raise DeliveryIndexError("delivery_channel must be organizers_only")
    sent_or_better = all(row["status"] in {"sent", "received"} for row in packs)
    ready = sent_or_better and bool(trial["independent_test"])
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "deadline": DEADLINE,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "precision_claim_publishable": PRECISION_PUBLISHABLE,
        "is_accuracy": False,
        "git_hosts_reports": False,
        "seed_fixture_on_trial": False,
        "samolet_direct_contact": False,
        "delivery_channel": DELIVERY_CHANNEL,
        "customer_deadline_is_final": True,
        "post_deadline_slot_is_not_delivery": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "packs": packs,
        "trial": trial,
        "ready_for_deadline": ready,
    }
