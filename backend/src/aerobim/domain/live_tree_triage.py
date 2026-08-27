"""Live-tree Red Team triage 2026-08-27 — attacks, not RT CLOSED.

Checkpoint NO_GO. Diff vs main was empty; this is a coverage pin of
KILL/HOLD/ACCEPT brakes. Does not raise IFC cap. Does not parse RVT/NWD/LIRA.
"""

from __future__ import annotations

from typing import Final

CLAIM_LEVEL: Final = "coverage_map_only"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "Live-tree Red Team triage. Not customer precision. Not TZ v1 as a "
    "product score. MIK act uses interim 0.60. Checkpoint NO_GO. "
    "closes_rt001/002/003=false."
)

# Verdict is KILL / HOLD / ACCEPT. Brake is the code or speech stop, not a fix of RT.
TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-V1-01",
        "verdict": "KILL",
        "attack": "Cite TZ v1 clash/nonconformity target as a measured AeroBIM score",
        "brake": "mik_act_may_cite_tz_v1_accuracy_as_measured() is False; IUA SAM-10",
    },
    {
        "id": "RT-V1-02",
        "verdict": "KILL",
        "attack": "Glue v1 brief, v2 TR, seven TechLab tasks, and house design TZ",
        "brake": "PAPER_OBJECTS length 4; snapshot not_the_same_as",
    },
    {
        "id": "RT-V1-03",
        "verdict": "KILL",
        "attack": "Commit the 6-page PDF binary or treat its sha256 as NDA pack_hash",
        "brake": "binary_in_git False; snapshot has no customer pack_hash",
    },
    {
        "id": "RT-V1-04",
        "verdict": "KILL",
        "attack": "MIK act cites v1 accuracy instead of interim 0.60",
        "brake": "pilot_interim_precision 0.60; mik_act_horizon interim_tp_fp_ge_0_60",
    },
    {
        "id": "RT-INJ-NEST",
        "verdict": "KILL",
        "attack": "inject_defects output nested in source rmtree/mutates the pack",
        "brake": "_reject_unsafe_inject_trees refuses equal and nested trees",
    },
    {
        "id": "RT-INJ-NDA",
        "verdict": "KILL",
        "attack": "inject_defects source is samples/customer or repo files/",
        "brake": "posix markers /samples/customer and /aerobim/files/",
    },
    {
        "id": "RT-KIT-01",
        "verdict": "KILL",
        "attack": "Re-introduce kitchen site tokens into the public tree",
        "brake": "lint_claims _KITCHEN_TOKENS including the 2026-08-27 addition",
    },
    {
        "id": "RT-SEAM-HOLD",
        "verdict": "HOLD",
        "attack": "Reopen RT-SEAM-01…18 / RT-CART-01…08 as if this pass closed them",
        "brake": "TZ_SEAM_COVERAGE_MAP §5 still Uncertain / coverage_map_only",
    },
    {
        "id": "RT-FULL-D01",
        "verdict": "HOLD",
        "attack": "POST /v1/validate/ifc greens under development sign-off in production",
        "brake": "DI injects settings.signoff_profile; soft passed is non-authoritative",
    },
    {
        "id": "RT-AGR-002",
        "verdict": "HOLD",
        "attack": "moscow_agr_2026 status=approved means Samolet customer_approved",
        "brake": "RT-002a city pack; RT-002b OPEN; profile not customer-hard",
    },
    {
        "id": "RT-ADR-001",
        "verdict": "ACCEPT",
        "attack": "LLM/VLM writes summary.passed",
        "brake": "DeterminismGate demotes advisory to INFO; never flips passed",
    },
    {
        "id": "RT-CAP-IFC",
        "verdict": "ACCEPT",
        "attack": "Raise AEROBIM_MAX_IFC_BYTES because one AR file is over cap",
        "brake": "default stays 256 MiB; owner flag only",
    },
)


def triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "live_tree_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = ["CLAIM_BOUNDARY", "CHECKPOINT", "TRIAGE_ROWS", "triage_snapshot"]
