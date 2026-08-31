"""Channel pack Red Team triage — 2026-08-31.

Attacks on the local unpack inventory, family facts, and CC-2/CC-4
shortlist. Not RT CLOSED. Uncompressed GiB, names, hashes stay .local (OA-9).
Path must not contain the hyphenated token blocked by pre-commit.
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.pack_family_facts import pack_family_snapshot

CLAIM_LEVEL: Final = "coverage_map_only"
CHECKPOINT: Final = "NO_GO"
CLAIM_BOUNDARY: Final = (
    "Channel-pack Red Team triage after the 31.08 unpack walk. "
    "Calc binaries are the majority of unpack bytes; that is inventory, "
    "not a solver. Token shortlists are not CC-2 MATCH. Uncompressed byte "
    "totals stay out of git. Not pack processed. Checkpoint NO_GO."
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-PACK-PROCESSED",
        "verdict": "KILL",
        "attack": "Hashed inventory of 6408 files means the pack is processed",
        "brake": "processed False; pack_probe claim_level local_inventory_not_processed",
    },
    {
        "id": "RT-PACK-43GB",
        "verdict": "KILL",
        "attack": "Quote the tracker title 43 GB as this measurement or as processed",
        "brake": "43 GB is the assigned task title; live unpack is a different count",
    },
    {
        "id": "RT-PACK-GIB",
        "verdict": "KILL",
        "attack": "Publish uncompressed byte totals of the NDA tree in git before OA-9",
        "brake": "uncompressed_gib_in_git False; byte-share is a boolean majority only",
    },
    {
        "id": "RT-PACK-LIRA-SOLVE",
        "verdict": "KILL",
        "attack": "Named .lir / f74 / tilde sidecars mean we recalculated the structure",
        "brake": "parse_lira False; calculation_correctness NOT_IMPLEMENTED; IUA TL-10",
    },
    {
        "id": "RT-PACK-TOKEN-MATCH",
        "verdict": "KILL",
        "attack": "6 docx class-phrase files or 46 xlsx load-token files are CC-2/CC-4 MATCH",
        "brake": "is_cc2_match False; compare_declared_tables needs an owner-canonical note",
    },
    {
        "id": "RT-PACK-NAIVE-B",
        "verdict": "KILL",
        "attack": "Bare B67/B56 tokens in every docx are concrete classes",
        "brake": "Context window ±160 around бетон/класс; naive regex is axes/marks",
    },
    {
        "id": "RT-PACK-IFC-RERUN",
        "verdict": "KILL",
        "attack": "4 unpack IFC copies are a new SIG-01 volume",
        "brake": "unique_ifc_already_analyzed 15; copies are size-matched, not a second pack",
    },
    {
        "id": "RT-PACK-STD-DEFECT",
        "verdict": "KILL",
        "attack": "The corporate Standard tree is a PD defect list",
        "brake": "TechLab task 2 carrier; customer_confirmed_patterns 0",
    },
    {
        "id": "RT-PACK-MAX-EVIDENCE",
        "verdict": "KILL",
        "attack": "3ds Max / images / CAD locks are project evidence",
        "brake": "Exclude from SIG-02 priority 1; render assets are not RD/BIM compare",
    },
    {
        "id": "RT-PACK-DXF-DWG",
        "verdict": "KILL",
        "attack": "321 ASCII DXF files make native DWG ready",
        "brake": "DXF is partial; DWG stays fail-closed; IUA SAM-04",
    },
    {
        "id": "RT-PACK-OCR",
        "verdict": "KILL",
        "attack": "728 scan-like PDFs are OCR-delivered findings",
        "brake": "HITL queue only; owner decides OCR budget; IUA SAM-03",
    },
    {
        "id": "RT-PACK-SCAN-FINDING",
        "verdict": "KILL",
        "attack": "PDF HITL rows from scans are drawing findings / door counts",
        "brake": "service_hitl; drawing_annotation_count 0 on the SIG-01 sample",
    },
    {
        "id": "RT-PACK-PP87",
        "verdict": "KILL",
        "attack": "ПЗ/АР/КР/КЖ tokens on paths are statutory PP-87 completeness",
        "brake": "pd_filename_inventory statutory_pp87 False",
    },
    {
        "id": "RT-PACK-RD",
        "verdict": "KILL",
        "attack": "PD↔RD pairing is runnable because the pack is large",
        "brake": "tz_class_2_rd_files 0; pack is PD",
    },
    {
        "id": "RT-PACK-MEETS",
        "verdict": "KILL",
        "attack": "Family facts license Meets/Does-not on the seven TechLab tasks",
        "brake": "seven_task_criterion Uncertain; detected_count 0",
    },
    {
        "id": "RT-PACK-HASH-GIT",
        "verdict": "KILL",
        "attack": "Commit pack-local.json / pack-tracker.tsv (names and sha256)",
        "brake": "OA-9; require_local_only_output; names_in_git False",
    },
    {
        "id": "RT-PACK-TXT-STUB",
        "verdict": "KILL",
        "attack": "Treat the small .local/pack txt tree as the Samolet construction pack",
        "brake": "Live carriers are the unpack tree; stub is not the NDA BIM set",
    },
    {
        "id": "RT-PACK-VOLUME-F1",
        "verdict": "KILL",
        "attack": "Mix SIG-01 machine-record volume with fixture F1 or the catalog",
        "brake": "publishable_finding_count 0; customer_confirmed_patterns 0",
    },
    {
        "id": "RT-PACK-OOXML-PARSE",
        "verdict": "HOLD",
        "attack": "Parse 46 xlsx into DeclaredCalcRow now and call it CC-4 delivered",
        "brake": "Next local step under .local; MATCH waits on owner-canonical note",
    },
    {
        "id": "RT-PACK-OA9-SHARE",
        "verdict": "HOLD",
        "attack": "Paste name-free aggregates to the tracker chat before OA-9 reply",
        "brake": "Owner pastes after written data regime; git already has census pins",
    },
    {
        "id": "RT-PACK-OCR-BUDGET",
        "verdict": "HOLD",
        "attack": "Commit to OCR on 728 scan-like PDFs this sprint",
        "brake": "Owner budget; engine stays HITL without an OCR claim",
    },
    {
        "id": "RT-PACK-CENSUS-MATCH",
        "verdict": "ACCEPT",
        "attack": "31.08 live walk disagrees with the 30.08 evening pin",
        "brake": "live_walk_matched_evening_pin True; unpack_file_count 6408",
    },
    {
        "id": "RT-PACK-HASH-LOCAL",
        "verdict": "ACCEPT",
        "attack": "SIG-02 hashed TSV cannot exist because OA-9 forbids hashes",
        "brake": "Hashes stay under .local; aggregate has hashes_in_output False",
    },
    {
        "id": "RT-PACK-CLASS-SHORTLIST",
        "verdict": "ACCEPT",
        "attack": "No readable CC-2 substrate exists on the pack",
        "brake": "docx_with_class_phrase 6; KR IFC already shows B25/B35 tokens",
    },
    {
        "id": "RT-PACK-DXF-ASCII",
        "verdict": "ACCEPT",
        "attack": "DXF on this pack is binary and unreadable",
        "brake": "dxf_all_ascii True; still partial, not DWG-ready",
    },
)


def pack_triage_snapshot() -> dict[str, object]:
    family = pack_family_snapshot()
    return {
        "artifact_type": "channel_pack_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_pack_processed": False,
        "uncompressed_gib_in_git": family["uncompressed_gib_in_git"],
        "calc_binaries_majority_of_unpack_bytes": family[
            "calc_binaries_majority_of_unpack_bytes"
        ],
        "is_cc2_match": family["is_cc2_match"],
        "seven_task_criterion": "Uncertain",
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
        "family": family,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "TRIAGE_ROWS",
    "pack_triage_snapshot",
]
