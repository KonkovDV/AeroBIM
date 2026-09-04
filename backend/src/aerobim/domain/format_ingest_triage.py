"""Format-ingest Red Team triage — 2026-09-01.

Seven strategy classes for closed CAD/solver files. Path must not contain
the hyphenated token blocked by pre-commit. Not a DWG product.
Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

from typing import Final

from aerobim.domain.checkpoint import CHECKPOINT

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Format-ingest Red Team triage after the 01.09 academic option map. "
    "KT#3 exchange object is IFC + PDF/A. Closed Autodesk CAD and .lir stay "
    "fail-closed. ODA trial is measurement, not a product. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)

KT3_RECOMMENDED: Final[dict[str, str]] = {
    "ifc": "primary_shared_gate",
    "pdf": "vector_text_plus_hitl_scans",
    "dxf": "optional_ezdxf_not_dwg",
    "dwg": "fail_closed_pdf_same_mark",
    "rvt": "fail_closed_ask_ifc_export",
    "nwd": "fail_closed_ask_federation_ifc",
    "lir": "compare_notes_not_parse",
}

STRATEGY_CLASSES: Final[tuple[str, ...]] = (
    "appointing_party_exchange",
    "licensed_sdk",
    "reverse_engineering",
    "converter_sidecar",
    "document_proxy",
    "hitl_or_missing",
    "written_out",
)

TRIAGE_ROWS: Final[tuple[dict[str, str], ...]] = (
    {
        "id": "RT-FMT-DWG-PRODUCT",
        "verdict": "KILL",
        "attack": "Any DWG path (ODA, CADSoftTools, ezdxf+FC) means a DWG product",
        "brake": "capabilities.dwg_dxf never OK; ADR-003 native DWG stays FAILED",
    },
    {
        "id": "RT-FMT-PARSE-NWD",
        "verdict": "KILL",
        "attack": "Write a Python NWD reader because files exist on the local tree",
        "brake": "No public NWD spec; presence is not a reader; fail-closed upload",
    },
    {
        "id": "RT-FMT-NAVIS-IFC",
        "verdict": "KILL",
        "attack": "Navisworks UI/API already writes IFC so we can skip the ask",
        "brake": "Stock Navisworks does not export IFC; plugins need their seat",
    },
    {
        "id": "RT-FMT-PARSE-LIR",
        "verdict": "KILL",
        "attack": "Parse .lir or ship an independent FEM as SIG-06",
        "brake": "native_lir not_implemented; four checks vs a readable note",
    },
    {
        "id": "RT-FMT-SUSTAINING-RVT",
        "verdict": "KILL",
        "attack": "ODA Sustaining 7500 USD buys native RVT/NWD",
        "brake": "BimRv and BimNv are separate 6250 USD extensions",
    },
    {
        "id": "RT-FMT-LIBREDWG",
        "verdict": "KILL",
        "attack": "Link LibreDWG into the MIT core as a free DWG adapter",
        "brake": "GPL-3+ copyleft; ADR-002 does not open a LICENSE change",
    },
    {
        "id": "RT-FMT-EZDXF-DWG",
        "verdict": "KILL",
        "attack": "ezdxf on ASCII DXF is native DWG ingest",
        "brake": "ezdxf is MIT DXF; DWG needs ODA File Converter, a different licence",
    },
    {
        "id": "RT-FMT-OCR-DONE",
        "verdict": "KILL",
        "attack": "Scan-like PDF volume means OCR is delivered",
        "brake": "Vector overlay is in git; scans remain HITL; cv_human_level MISSING",
    },
    {
        "id": "RT-FMT-BENCH-OURS",
        "verdict": "KILL",
        "attack": "Quote DrawingVQA 94.9 or Appl. Sci. 91 as AeroBIM accuracy",
        "brake": "Those scores are foreign corpora; RT-001 stays OPEN",
    },
    {
        "id": "RT-FMT-ODA-PRODUCT",
        "verdict": "KILL",
        "attack": "A 60-day ODA trial is a DWG product feature on the jury map",
        "brake": "ADR-003: trial is fact-finding; claim_allowed stays false",
    },
    {
        "id": "RT-FMT-ADSK-BUY",
        "verdict": "KILL",
        "attack": "Buy Revit/Navisworks API for a Russian legal entity this window",
        "brake": "Autodesk channel paused 2022+; not a KT#3 procurement path",
    },
    {
        "id": "RT-FMT-RAISE-SPF",
        "verdict": "KILL",
        "attack": "Raise SPF 256 MiB so native CAD ingest becomes tractable",
        "brake": "SPF cap is in-memory IFC; natives are a format class, not a size class",
    },
    {
        "id": "RT-FMT-ODA-TRIAL",
        "verdict": "HOLD",
        "attack": "Skip the Drawings trial so proxy/SHX losses stay unmeasured",
        "brake": "ADR-003 allows a 60-day measurement; claim_allowed stays false",
    },
    {
        "id": "RT-FMT-SDK-SIGN",
        "verdict": "HOLD",
        "attack": "Buy Sustaining+BimRv+BimNv before a signed Samolet profile",
        "brake": "ADR-003 buy rule: DWG-only share plus signed profile, then owner",
    },
    {
        "id": "RT-FMT-GPL-PROC",
        "verdict": "HOLD",
        "attack": "Run LibreDWG as a sidecar process to dodge copyleft",
        "brake": "Legal fork, not engineering; do not ship without a license ADR",
    },
    {
        "id": "RT-FMT-EXCHANGE",
        "verdict": "ACCEPT",
        "attack": "TZ 1.1.5 silence looks like an unmet native-RVT item",
        "brake": "PP 614 / 783/pr: PDF/A + IFC is the machine-checkable contour",
    },
    {
        "id": "RT-FMT-FAIL-CLOSED",
        "verdict": "ACCEPT",
        "attack": "HTTP quietly skips .rvt/.nwd/.dwg/.lir inside ZIP",
        "brake": "Upload and ZIP members fail-closed; DXF sibling does not clear it",
    },
    {
        "id": "RT-FMT-CC-NOTE",
        "verdict": "ACCEPT",
        "attack": "No LIRA path at all on the eight-task card",
        "brake": "CC-2/CC-4 methodology vs a readable note; not a solver",
    },
    {
        "id": "RT-FMT-SEVEN",
        "verdict": "ACCEPT",
        "attack": "Only A/B/C DWG options exist; NWD/LIRA have no decision map",
        "brake": "Seven strategy classes cover every closed format on the pack",
    },
)


def format_ingest_triage_snapshot() -> dict[str, object]:
    return {
        "artifact_type": "format_ingest_red_team_triage",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "detected_count": 0,
        "is_accuracy": False,
        "is_dwg_ready": False,
        "is_native_rvt": False,
        "is_native_nwd": False,
        "is_lira_solver": False,
        "navisworks_stock_ifc_export": False,
        "kt3_recommended": dict(KT3_RECOMMENDED),
        "strategy_classes": list(STRATEGY_CLASSES),
        "rows": [dict(row) for row in TRIAGE_ROWS],
        "kill_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "KILL"),
        "hold_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "HOLD"),
        "accept_count": sum(1 for row in TRIAGE_ROWS if row["verdict"] == "ACCEPT"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "KT3_RECOMMENDED",
    "STRATEGY_CLASSES",
    "TRIAGE_ROWS",
    "format_ingest_triage_snapshot",
]
