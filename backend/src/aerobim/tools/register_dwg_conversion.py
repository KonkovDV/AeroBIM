"""Register a DWG→derived conversion pair as a hash-bound provenance sidecar.

DWG conversion MVP (FOUR_DIRECTION_GAP_ANALYSIS §1.3, steps 2–3): after an
**external** conversion (customer or agreed tool), the operator registers the
``source_dwg_sha256 ↔ derived_sha256`` pair. The sidecar is re-verified right
after writing (in-toto/SLSA posture: declared provenance counts only when it
recomputes). This never claims native DWG support — ``dwg_dxf`` stays non-OK.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.domain.cad_conversion_qa import (
    ConversionQaPolicy,
    conversion_qa_section_payload,
)
from aerobim.domain.derived_cad_provenance import (
    DERIVED_NOT_NATIVE_CLAIM,
    build_derived_cad_provenance,
    derived_provenance_sidecar_payload,
    verify_derived_provenance_sidecar,
)


def register_dwg_conversion(
    *,
    source_dwg: Path,
    derived: Path,
    derived_format: str,
    conversion_tool: str | None,
    conversion_tool_version: str | None,
    loss_notes: tuple[str, ...] | None,
    qa_section: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build, write and immediately re-verify the sidecar next to the DWG."""

    if not source_dwg.is_file():
        raise FileNotFoundError(source_dwg)
    # Absolute paths make the sidecar independent of the operator's CWD; the
    # verifier still jails them to the package directory at analyze time.
    source_dwg = source_dwg.resolve()
    derived = derived.resolve()
    provenance = build_derived_cad_provenance(
        source_dwg=source_dwg,
        derived=derived,
        derived_format=derived_format,
        conversion_tool=conversion_tool,
        conversion_tool_version=conversion_tool_version,
        loss_notes=loss_notes,
    )
    payload = derived_provenance_sidecar_payload(provenance)
    if qa_section is not None:
        payload["conversion_qa"] = qa_section
    sidecar = source_dwg.with_name(source_dwg.name + ".derived-provenance.json")
    sidecar.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verification = verify_derived_provenance_sidecar(sidecar)
    qa = verification.conversion_qa
    return {
        "artifact_type": "aerobim_dwg_conversion_registration",
        "schema_version": "1.1.0",
        "sidecar_path": str(sidecar),
        "source_dwg_sha256": provenance.source_dwg_sha256,
        "derived_sha256": provenance.derived_sha256,
        "derived_format": provenance.derived_format,
        "verified": verification.verified,
        "mismatches": list(verification.mismatches),
        "conversion_qa_status": qa.status if qa is not None else None,
        "conversion_qa_reasons": list(qa.reasons) if qa is not None else [],
        "claim_boundary": DERIVED_NOT_NATIVE_CLAIM,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dwg", type=Path, required=True)
    parser.add_argument("--derived", type=Path, required=True)
    parser.add_argument("--derived-format", choices=("pdf", "ifc", "dxf"), required=True)
    parser.add_argument("--tool", default=None, help="external conversion tool name")
    parser.add_argument("--tool-version", default=None)
    parser.add_argument(
        "--loss-note",
        action="append",
        default=None,
        help="observed conversion loss (repeatable); defaults to the known-loss list",
    )
    parser.add_argument(
        "--expected-sheet",
        action="append",
        default=None,
        help="agreed expected sheet name (repeatable); enables conversion QA",
    )
    parser.add_argument(
        "--expected-layer",
        action="append",
        default=None,
        help="agreed expected layer name (repeatable); enables conversion QA",
    )
    parser.add_argument("--observed-sheet", action="append", default=None)
    parser.add_argument("--observed-layer", action="append", default=None)
    parser.add_argument(
        "--max-layer-loss-ratio",
        type=float,
        default=0.0,
        help="layer-loss share above which the conversion fails (default 0.0 = strict)",
    )
    args = parser.parse_args(argv)

    qa_section: dict[str, object] | None = None
    if args.expected_sheet or args.expected_layer:
        qa_section = conversion_qa_section_payload(
            expected_sheets=tuple(args.expected_sheet or ()),
            expected_layers=tuple(args.expected_layer or ()),
            observed_sheets=tuple(args.observed_sheet or ()),
            observed_layers=tuple(args.observed_layer or ()),
            policy=ConversionQaPolicy(max_layer_loss_ratio=args.max_layer_loss_ratio),
        )

    try:
        report = register_dwg_conversion(
            source_dwg=args.source_dwg,
            derived=args.derived,
            derived_format=args.derived_format,
            conversion_tool=args.tool,
            conversion_tool_version=args.tool_version,
            loss_notes=tuple(args.loss_note) if args.loss_note else None,
            qa_section=qa_section,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
