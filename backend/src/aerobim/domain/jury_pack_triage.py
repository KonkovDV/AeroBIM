"""Jury-pack Red Team triage — 2026-09-01.

Attacks on the public GitHub tree as read by selection commission no. 7
(roles, not names). Path must not contain the hyphenated token blocked
by pre-commit. Not RT CLOSED. Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Jury-pack Red Team triage after the kitchen-surface pass. "
    "Roles not FIO. Unpack counts stay off TIER0. Not pack processed. "
    "Not sitting-member OSINT in git. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)

# Surfaces a sitting member is expected to open first. Fingerprint counts
# and personal names stay off these paths.
JURY_SURFACES: Final[tuple[str, ...]] = (
    "docs/TIER0_INDEX.md",
    "docs/docs.md",
    "docs/quality/MIK_SEAT_BRIEFS_2026_08.md",
    "docs/quality/TRACKER_EIGHT_TASKS_2026_08.md",
    "docs/quality/KT3_IN_REPO_WORKPLAN_2026_08_27.md",
    "docs/evidence/DATA_STATEMENT_2026_08.md",
    "docs/demo/KT3_JURY_FAQ_2026_08_25.md",
    "docs/demo/KT3_OPERATOR_RUNBOOK_2026_08_25.md",
    "docs/demo/KT3_TRACKER_SIX_TASKS_2026_08.md",
    "docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md",
    "docs/quality/JURY_PACK_TRIAGE_2026_09.md",
    "docs/quality/FORMAT_INGEST_TRIAGE_2026_09.md",
    "docs/quality/UI_EXPERT_WORKPLACE_TRIAGE_2026_09.md",
    "docs/quality/K4_COMMERCIAL_PATH_2026_08.md",
    "docs/pilot-claim-boundary-2026.md",
    "docs/tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md",
    "docs/demo/KT3_RVT_NWD_CV_ONEPAGER_2026_08.md",
    "submission/README.md",
)

JURY_FINGERPRINT_TOKENS: Final[tuple[str, ...]] = (
    "6408",
    "2552",
    "10599",
    "6 docx",
    "46 xlsx",
    "SIGINEVICH",
    "TRACKER_DMITRY",
    "CHANNEL_SAMOLET_MAX_PASS",
    "Team Space",
    "GigaChat",
    "SPG_CONSTRUCTION_VS_FM",
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-JURY-FIO",
        "verdict": "KILL",
        "attack": "Commit sitting-member FIO or OSINT bios to the public tree",
        "brake": "Seat briefs are roles; three partner seats by agreement; OA-2",
    },
    {
        "id": "RT-JURY-HOMONYM",
        "verdict": "KILL",
        "attack": "Treat open-web homonyms as confirmed sitting members",
        "brake": "Partner seats stay by agreement; do not bind speech to a third-party bio",
    },
    {
        "id": "RT-JURY-TRACKER-NAME",
        "verdict": "KILL",
        "attack": "Keep tracker surname or given name in a git path or snapshot",
        "brake": "TRACKER_EIGHT_TASKS_2026_08; KT3_TRACKER_SIX_TASKS; snapshot has no person key",
    },
    {
        "id": "RT-JURY-TIER0-CENSUS",
        "verdict": "KILL",
        "attack": "Put unpack census / DWG / RVT fingerprint counts on TIER0 or docs.md",
        "brake": "Census and family facts are engineering pins, not jury exhibits",
    },
    {
        "id": "RT-JURY-TIER0-SHORTLIST",
        "verdict": "KILL",
        "attack": "Quote the Office shortlist counts on the TIER0-linked eight-task card",
        "brake": "TRACKER_EIGHT SIG-06 says shortlist not MATCH without those counts",
    },
    {
        "id": "RT-JURY-PROCESSED",
        "verdict": "KILL",
        "attack": "Read any local inventory as pack processed",
        "brake": "processed False; publishable_finding_count 0",
    },
    {
        "id": "RT-JURY-TANGL",
        "verdict": "KILL",
        "attack": "Pitch AeroBIM as a Tangl replacement to the BIM seat",
        "brake": "Seat brief: 10D attributes; Tangl is the model layer; we are the document seam",
    },
    {
        "id": "RT-JURY-GIGACHAT",
        "verdict": "KILL",
        "attack": "Leave Team Space / GigaChat process notes on the eight-task SSOT",
        "brake": "SSOT says unsynced chat copies are not used; no vendor chat name",
    },
    {
        "id": "RT-JURY-CHANNEL-BRAND",
        "verdict": "KILL",
        "attack": "Keep CHANNEL_SAMOLET_MAX_PASS in a public path",
        "brake": "Renamed CHANNEL_LOCAL_MAX_PASS; not a jury exhibit",
    },
    {
        "id": "RT-JURY-OSINT-GIT",
        "verdict": "KILL",
        "attack": "Track the Samolet OSINT vector or other session kitchen",
        "brake": "docs/gtm/SAMOLET_OSINT_VECTOR* gitignored; honesty lock unpublished list",
    },
    {
        "id": "RT-JURY-LOCAL-PIN",
        "verdict": "KILL",
        "attack": "Commit a locally minted IFC-schema or runtime pin as attested_by=ci",
        "brake": "Pre-push warns; attested_by=ci only; local timings stay unstaged",
    },
    {
        "id": "RT-JURY-GIB",
        "verdict": "KILL",
        "attack": "Publish uncompressed NDA byte totals on a jury surface",
        "brake": "uncompressed_gib_in_git False; majority boolean only",
    },
    {
        "id": "RT-JURY-QUESTION-EXHIBIT",
        "verdict": "KILL",
        "attack": "Put the unsent customer question pack on TIER0",
        "brake": "Draft stays in partners/; TIER0 no longer lists it",
    },
    {
        "id": "RT-JURY-OA-EXHIBIT",
        "verdict": "KILL",
        "attack": "Present OWNER_ACTIONS as a jury exhibit of work already done",
        "brake": "Owner list is off TIER0; rows are not marked done",
    },
    {
        "id": "RT-JURY-MEETS",
        "verdict": "KILL",
        "attack": "Infer Meets/Does-not on seven TechLab tasks from family facts",
        "brake": "seven_task_criterion Uncertain; local max-pass is not a verdict",
    },
    {
        "id": "RT-JURY-ENG-PINS",
        "verdict": "HOLD",
        "attack": "Delete census JSON from git so the processed-claim brake disappears",
        "brake": "Keep engineering pins; mark not a jury exhibit; counts stay off TIER0",
    },
    {
        "id": "RT-JURY-DENYLIST",
        "verdict": "HOLD",
        "attack": "Add commission surnames to the kitchen denylist in this commit",
        "brake": "HMAC pin is CI-secret; owner rotates secrets out of band",
    },
    {
        "id": "RT-JURY-SEATS-ROLES",
        "verdict": "ACCEPT",
        "attack": "Jury map has no role briefs so speech invents FIO",
        "brake": "MIK_SEAT_BRIEFS on TIER0; FIO clause present",
    },
    {
        "id": "RT-JURY-RENAME",
        "verdict": "ACCEPT",
        "attack": "Tracker personal names remain in git ls-files",
        "brake": "Honesty lock forbids old tracker and channel-brand path tokens",
    },
    {
        "id": "RT-JURY-TIER0-SHRINK",
        "verdict": "ACCEPT",
        "attack": "TIER0 still advertises census / family / local max-pass / SIG-01 volume",
        "brake": "Those files are off TIER0; intro says not a jury exhibit",
    },
    {
        "id": "RT-JURY-OSINT-IGNORED",
        "verdict": "ACCEPT",
        "attack": "Session OSINT vector is a tracked GitHub file",
        "brake": "SAMOLET_OSINT_VECTOR stays gitignored; unpublished-list honesty lock",
    },
    {
        "id": "RT-JURY-NOT-EXHIBIT",
        "verdict": "ACCEPT",
        "attack": "Engineering pins look like a jury exhibit because TIER0 listed them",
        "brake": "TIER0 intro: census / family / local max-pass are not the jury map",
    },
    {
        "id": "RT-JURY-SPG-HOP",
        "verdict": "KILL",
        "attack": "Hop from TIER0 or the eight-task card to the SPG 49% TIM pin",
        "brake": "Consulting pin stays; filename off jury surfaces and off TIER0",
    },
    {
        "id": "RT-JURY-UI-LIVE",
        "verdict": "KILL",
        "attack": "Hop from the TIER0 UI pin to workplace delivered or Checkpoint GO",
        "brake": "Pin says review shell; KT#3 laptop track stays CLI",
    },
    {
        "id": "RT-JURY-TZ-UI-DONE",
        "verdict": "KILL",
        "attack": "Read TZ matrix Web UI done as a sitting-member exhibit of delivery",
        "brake": "Matrix row is partial; UI pin is the SSOT",
    },
)


def jury_pack_triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "jury_pack_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_pack_processed": False,
        "names_in_git": False,
        "sitting_member_list_in_git": False,
        "seven_task_criterion": "Uncertain",
        "jury_surfaces": list(JURY_SURFACES),
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "JURY_FINGERPRINT_TOKENS",
    "JURY_SURFACES",
    "TRIAGE_ROWS",
    "jury_pack_triage_snapshot",
]
