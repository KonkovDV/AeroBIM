"""Tracker Dmitry (TechLab) — six sprint tasks as they apply to KT#3.

Assigned 14.08.2026 ~15:26. KT#2 was 20.08; KT#3 window is 03–21.09.
These rows are operational hygiene, not customer precision and not Checkpoint GO.
"""

from __future__ import annotations

from typing import Any, Final

CLAIM_LEVEL: Final = "operational_hygiene"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "Tracker six-task status for KT#3. Live fixture CLI and open-bench pins. "
    "Not product accuracy. Not customer SLA. Not a scheduled-demo count in git. "
    "Checkpoint NO_GO. closes_rt001/002/003=false."
)
TRACKER_NAME: Final = "Dmitry"
ASSIGNED_AT: Final = "2026-08-14"
KT3_WINDOW: Final = "2026-09-03..2026-09-21"

# agent = what the repo can show; owner = what git must not invent.
TRACKER_TASKS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "TRK-01",
        "title": "Product for KT#3: live fail-closed CLI on a fixture",
        "agent": "done_fixture",
        "owner": "n/a",
        "kt3_show": "python -m aerobim.tools.run_kt3_jury",
        "stop": "Checkpoint GO / market GO = customer GO",
    },
    {
        "id": "TRK-02",
        "title": "IFC2X3 / IFC4 / IFC4X3 kernel table",
        "agent": "done_fixture",
        "owner": "blocked_customer_packs",
        "kt3_show": "docs/evidence/ifc-release-matrix-2026-08.md",
        "stop": "Product accuracy by IFC release",
    },
    {
        "id": "TRK-03",
        "title": "Open datasets searched and run (honest countable subsets)",
        "agent": "done_open_bench",
        "owner": "blocked_pd_expertise_corpus",
        "kt3_show": "docs/demo/KT2_CORPUS_SSOT_2026_08.md",
        "stop": "Open bench = RT-001 CLOSED",
    },
    {
        "id": "TRK-04",
        "title": "Scientific consultant / IT mentor questions in the repo",
        "agent": "done_speech",
        "owner": "blocked_consultation_minutes",
        "kt3_show": "docs/demo/KT3_JURY_FAQ_2026_08_25.md",
        "stop": "Invented consultation minutes",
    },
    {
        "id": "TRK-05",
        "title": "KPI = scheduled demos (3–5)",
        "agent": "local_only",
        "owner": "blocked_funnel_in_git",
        "kt3_show": "owner file outside git",
        "stop": "Scheduled-demo count as a git fact",
    },
    {
        "id": "TRK-06",
        "title": "Monetization with MIT open core",
        "agent": "adr_accepted",
        "owner": "blocked_commercial_decision",
        "kt3_show": "docs/architecture/ADR-002-open-core-commercial-boundary-2026.md",
        "stop": "Tracker agreed Tangl/10D/SKU in code",
    },
)

SPEECH_TANGLE: Final = (
    "Tangl is the model layer; AeroBIM is the pack seam (requirements ↔ IFC ↔ sheets ↔ revisions)."
)


def tracker_snapshot() -> dict[str, Any]:
    items = [dict(row) for row in TRACKER_TASKS]
    return {
        "artifact_type": "tracker_six_tasks_kt3",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "tracker": TRACKER_NAME,
        "assigned_at": ASSIGNED_AT,
        "kt3_window": KT3_WINDOW,
        "speech_tangl": SPEECH_TANGLE,
        "scheduled_demos_in_git": False,
        "items": items,
        "item_count": len(items),
        "agent_done_count": sum(1 for row in items if row["agent"].startswith(("done", "adr"))),
        "owner_blocked_count": sum(1 for row in items if row["owner"].startswith("blocked")),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "SPEECH_TANGLE",
    "TRACKER_TASKS",
    "tracker_snapshot",
]
