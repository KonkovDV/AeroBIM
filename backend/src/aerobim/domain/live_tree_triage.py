"""Live-tree Red Team triage 2026-08-27 — attacks, not RT CLOSED.

Pass 1: TZ v1 / inject_defects / kitchen tokens.
Pass 2: KT#3 jury CLI, tracker six tasks, unsigned OOS, owner inventory.
Pass 3: OOS manifest gate, remark storey/axis from IfcSpatialIndex, packs/day not SLA.
Pass 4: 25.08 channel speech, analyze cap vs ingest, axis not nearest-grid, OIDC BFF, RT-002b.
Pass 5: xlsx/docx table MATCH ≠ solver; PDF LIRA fragile; streaming design ≠ raised cap.
Pass 6: HTTP .lir/.spr honesty reason; JSON sidecar ≠ disk R-tree.
Does not raise IFC cap. Does not parse RVT/NWD/LIRA.
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
        "brake": "lint_claims _KITCHEN_TOKENS (site toponyms + tracker surname)",
    },
    {
        "id": "RT-KT3-01",
        "verdict": "KILL",
        "attack": "Fixture passed=false or a live CLI means Checkpoint GO",
        "brake": "require_kt3_jury_gate rejects passed=True; checkpoint stays NO_GO",
    },
    {
        "id": "RT-KT3-02",
        "verdict": "KILL",
        "attack": "Lead the jury with REQ-AREA and a null GUID",
        "brake": "select_jury_finding skips REQ-AREA and empty GUIDs",
    },
    {
        "id": "RT-KT3-03",
        "verdict": "KILL",
        "attack": "Fixture mep_system_clash=OK means MEP delivered",
        "brake": "require_kt3_jury_gate rejects OK/DELIVERED",
    },
    {
        "id": "RT-TRK-05",
        "verdict": "KILL",
        "attack": "Publish scheduled-demo KPI 3-5 as a git fact",
        "brake": "scheduled_demos_in_git is False; require_honest_kt3_payload",
    },
    {
        "id": "RT-TRK-GO",
        "verdict": "KILL",
        "attack": "Tracker agent_done_count means six customer tasks closed",
        "brake": "owner_blocked_count >= 4; checkpoint NO_GO",
    },
    {
        "id": "RT-OOS-01",
        "verdict": "KILL",
        "attack": "Unsigned OOS licenses skip, or signed OOS closes RT",
        "brake": "evaluate_oos: unsigned does not license skip; accepted never closes RT",
    },
    {
        "id": "RT-INV-01",
        "verdict": "KILL",
        "attack": "Write files/ names or hashes into docs/ or samples/",
        "brake": "require_local_only_output; public rehearsal names_in_git False",
    },
    {
        "id": "RT-OOS-MANIFEST",
        "verdict": "KILL",
        "attack": "Leave samples/oos on disk but omit them from DATASET_MANIFEST",
        "brake": "test_samples_manifest_gate; export_samples_manifest --merge-missing",
    },
    {
        "id": "RT-REMARK-LOC",
        "verdict": "KILL",
        "attack": "Invent storey/axis from OCR, target_ref, or LLM text",
        "brake": "TemplateRemarkGenerator uses stamped storey_name/grid_axis from IfcSpatialIndex",
    },
    {
        "id": "RT-PACKS-SLA",
        "verdict": "KILL",
        "attack": "Treat customer-stated 5-10 packs/day as a measured SLA",
        "brake": "peak_packs_per_day_mvp is stated text; thresholds publishable_sla is false",
    },
    {
        "id": "RT-NODATA-SPEECH",
        "verdict": "KILL",
        "attack": "Say customer sent no data after the 25.08 channel",
        "brake": "share_url_received; speech_forbid_no_customer_data; pack not in git",
    },
    {
        "id": "RT-IFC-RAISE",
        "verdict": "KILL",
        "attack": "Raise default AEROBIM_MAX_IFC_BYTES to the stated 1.5 GB model cap",
        "brake": "analyze default stays 256 MiB; ingest caps are separate",
    },
    {
        "id": "RT-AXIS-NEAR",
        "verdict": "KILL",
        "attack": "Claim nearest IfcGrid intersection as axis in remarks",
        "brake": "IfcGridAxis.AxisTag only; nearest intersection is not implemented",
    },
    {
        "id": "RT-CLOUD-OIDC",
        "verdict": "KILL",
        "attack": "HTTPS closed-cloud ask means browser OIDC BFF is live",
        "brake": "auth_bff NOT_IMPLEMENTED; production BFF still 501",
    },
    {
        "id": "RT-002-SPPACK",
        "verdict": "KILL",
        "attack": "An unsigned SP 63/20 pack closes RT-002b / RT-002",
        "brake": "RT-002a city IDS; RT-002b needs Samolet signature; closes_rt002 false",
    },
    {
        "id": "RT-LIRA-SOLVER",
        "verdict": "KILL",
        "attack": "Treat xlsx/docx table MATCH as calculation_correctness",
        "brake": "compare_declared_tables solver not_implemented; native_lir closed",
    },
    {
        "id": "RT-PDF-LIRA",
        "verdict": "KILL",
        "attack": "Parse LIRA PDF as a declared table compare",
        "brake": "extract status pdf_fragile; SpreadsheetLoadEvidenceAdapter LIRA-PDF",
    },
    {
        "id": "RT-IFC-STREAM",
        "verdict": "KILL",
        "attack": "Treat streaming design as live disk R-tree or raised analyze cap",
        "brake": "streaming_design_snapshot raises_default_cap False; 256 MiB default",
    },
    {
        "id": "RT-ZIP-SNIFF",
        "verdict": "KILL",
        "attack": "ZIP namelist on sniff prefix turns zip-bomb into 415",
        "brake": "sniff is magic only; inspect_zip_path 422 then Autodesk/LIRA 415",
    },
    {
        "id": "RT-LIRA-HTTP",
        "verdict": "KILL",
        "attack": "HTTP .lir/.spr as generic disallowed extension hides honesty",
        "brake": "NATIVE_LIRA_CLOSED_REASON 415; ZIP members after inspect_zip_path",
    },
    {
        "id": "RT-SIDECAR-RTREE",
        "verdict": "KILL",
        "attack": "JSON sidecar of IfcSpatialIndex is a live disk R-tree",
        "brake": "disk_r_tree designed_not_implemented; sidecar dump_only; cap 256 MiB",
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
        "id": "RT-INV-HOLD",
        "verdict": "HOLD",
        "attack": "Public rehearsal 2383/15/1 counts are a pack_hash / RT-001 CLOSED",
        "brake": "coverage_map_only; no names/hashes; intake still blocked",
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
