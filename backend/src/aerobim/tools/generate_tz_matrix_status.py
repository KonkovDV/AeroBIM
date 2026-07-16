"""Generate TZ compliance status rows from runtime capabilities + evidence manifest (R3)."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.architecture import Contour
from aerobim.domain.models import CapabilityState, ReportCapabilities


def _status_from_capability(state: CapabilityState) -> str:
    if state is CapabilityState.OK:
        return "partial"  # ok on fixture ≠ customer-done
    if state is CapabilityState.FAILED:
        return "partial"
    return "missing"


def generate_tz_matrix_status(
    *,
    capabilities: ReportCapabilities | None = None,
    evidence_manifest: dict[str, object] | None = None,
) -> dict[str, object]:
    """Derive feature statuses; never hand-author done without customer evidence."""

    caps = capabilities or ReportCapabilities()
    evidence = evidence_manifest or {}
    customer_evidence = bool(evidence.get("customer_corpus_present"))
    rows = [
        {
            "requirement": "BIM IFC + IDS",
            "contour": Contour.DETERMINISTIC_VALIDATION.value,
            "capability": "ids",
            "status": "done"
            if caps.ids.status is CapabilityState.OK and customer_evidence
            else _status_from_capability(caps.ids.status)
            if caps.ids.status is not CapabilityState.SKIPPED
            else "partial",
            "note": "done only with customer corpus evidence",
        },
        {
            "requirement": "Norm / rule packs",
            "contour": Contour.DETERMINISTIC_VALIDATION.value,
            "capability": "norm_rule_packs",
            "status": "done"
            if caps.norm_rule_packs.status is CapabilityState.OK and customer_evidence
            else "partial",
            "note": "synthetic-template loader is partial until customer_approved pack",
        },
        {
            "requirement": "Section pairing PD↔RD",
            "contour": Contour.DETERMINISTIC_VALIDATION.value,
            "capability": "section_pairing",
            "status": _status_from_capability(caps.section_pairing.status)
            if caps.section_pairing.status is not CapabilityState.SKIPPED
            else "partial",
        },
        {
            "requirement": "Geometric clash",
            "contour": Contour.DETERMINISTIC_VALIDATION.value,
            "capability": "clash",
            "status": "partial",
            "note": "generic clash only; MEP-CLASH-001 open",
        },
        {
            "requirement": "MEP system intersections",
            "contour": Contour.DETERMINISTIC_VALIDATION.value,
            "capability": "clash",
            "status": "missing",
            "note": "blocked on federated MEP IFC + scope memo",
        },
        {
            "requirement": "CV / drawing literacy",
            "contour": Contour.AI_ADVISORY.value,
            "capability": "raster",
            "status": "missing",
            "note": "OCR baseline ≠ CV; advisory only",
        },
        {
            "requirement": "OCR baseline",
            "contour": Contour.INGESTION.value,
            "capability": "raster",
            "status": "partial",
        },
        {
            "requirement": "BCF / review HITL",
            "contour": Contour.EVIDENCE_REPORTING.value,
            "capability": None,
            "status": "partial",
        },
    ]
    return {
        "artifact_type": "aerobim_tz_matrix_status",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "author_relationship": "self",
        "corpus_kind": "fixture" if not customer_evidence else "customer",
        "customer_corpus_present": customer_evidence,
        "capabilities_snapshot": {
            name: asdict(getattr(caps, name))
            for name in (
                "clash",
                "ids",
                "ifc_validation",
                "unit_scale",
                "raster",
                "ifc_schema",
                "norm_rule_packs",
                "section_pairing",
            )
        },
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--customer-corpus",
        action="store_true",
        help="Mark evidence manifest as customer corpus present",
    )
    args = parser.parse_args(argv)
    payload = generate_tz_matrix_status(
        evidence_manifest={"customer_corpus_present": bool(args.customer_corpus)}
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
