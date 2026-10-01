"""Native RVT/NWD honesty probe — never a Revit/Navisworks-ready claim.

Closed Autodesk formats have no free reader in this MIT tree. Fail-closed
ingest is the product: NOT_IMPLEMENTED with a reason, not a silent skip.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from aerobim.domain.cad_ingest import (
    AUTODESK_NATIVE_SUFFIXES,
    NATIVE_AUTODESK_CLOSED_REASON,
    NAVISWORKS_STOCK_IFC_EXPORT,
)
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor


def probe_native_autodesk_toolchain() -> dict[str, Any]:
    """Return a fail-closed snapshot of native RVT/NWD tooling."""

    ingestor = EzdxfCadModelIngestor()
    samples: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for suffix in sorted(AUTODESK_NATIVE_SUFFIXES):
            path = root / f"probe{suffix}"
            path.write_bytes(b"not-an-autodesk-file")
            ingest = ingestor.ingest(path)
            samples[suffix] = {
                "supported": ingest.supported,
                "format_resolved": ingest.format_resolved,
                "reason": ingest.reason,
            }
    any_supported = any(bool(row["supported"]) for row in samples.values())
    return {
        "artifact_type": "native_autodesk_toolchain_probe",
        "schema_version": "1.0.0",
        "native_rvt_nwd": "missing",
        "rvt_native": "NOT_IMPLEMENTED",
        "nwd_native": "NOT_IMPLEMENTED",
        "claim_allowed": False,
        "navisworks_stock_ifc_export": NAVISWORKS_STOCK_IFC_EXPORT,
        "any_ingest_supported": any_supported,
        "suffix_probes": samples,
        "reason": NATIVE_AUTODESK_CLOSED_REASON,
        "claim_boundary": (
            "IFC 2x3/4/4x3 is the ingest path. Native RVT/NWD is the same class as "
            "native DWG: closed format, no free reader. Never rvt_supported / nwd_ready. "
            "Stock Navisworks does not write IFC."
        ),
        "ingest_route": "docs/tz/NATIVE_AUTODESK_INGEST_BOUNDARY_2026.md",
        "format_ingest": "docs/quality/FORMAT_INGEST_TRIAGE_2026_09.md",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON snapshot (stdout when omitted)",
    )
    args = parser.parse_args(argv)
    payload = probe_native_autodesk_toolchain()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
