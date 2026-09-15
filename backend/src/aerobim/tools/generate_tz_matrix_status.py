"""Generate TZ compliance status rows from runtime capabilities + evidence manifest (R3)."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.architecture import Contour
from aerobim.domain.checkpoint import checkpoint_fields
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
    evidence_path: str | None = None,
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
    if evidence_path:
        for row in rows:
            row["evidence_path"] = evidence_path
    payload: dict[str, object] = {
        "artifact_type": "aerobim_tz_matrix_status",
        "schema_version": "1.2.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "author_relationship": "self",
        "claim_boundary": (
            "Capability snapshot. Fixture OK ≠ customer done. "
            "Not product accuracy. Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
        ),
    }
    payload.update(checkpoint_fields())
    payload.update(
        {
            "interpretation_use": {
                "licensed_use": "engine_regression",
                "ledger": "docs/quality/INTERPRETATION_USE_LEDGER_2026_08.md",
                "closes_rt001": False,
            },
            "corpus_kind": "fixture" if not customer_evidence else "customer",
            "customer_corpus_present": customer_evidence,
            "evidence_path": evidence_path,
            "capabilities_executed": capabilities is not None,
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
    )
    return payload


def capabilities_from_fixture_pack(
    pack_path: Path, storage_dir: Path
) -> tuple[ReportCapabilities, str]:
    from aerobim.core.config.settings import Settings
    from aerobim.core.di.tokens import Tokens
    from aerobim.infrastructure.di.bootstrap import bootstrap_container
    from aerobim.tools.benchmark_project_package import load_benchmark_pack, repo_root

    pack = load_benchmark_pack(pack_path, repo_root())
    settings = Settings(
        application_name="aerobim-tz-matrix",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage_dir,
        debug=True,
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    container = bootstrap_container(settings)
    report = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE).execute(pack.request)
    return report.capabilities or ReportCapabilities(), pack.pack_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--customer-corpus",
        action="store_true",
        help="Mark evidence manifest as customer corpus present",
    )
    parser.add_argument(
        "--from-fixture",
        type=Path,
        default=None,
        help="Benchmark pack JSON; live analyze capabilities (still not customer done)",
    )
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)
    caps: ReportCapabilities | None = None
    evidence_path: str | None = None
    if args.from_fixture is not None:
        pack_path = args.from_fixture.resolve()
        with tempfile.TemporaryDirectory(prefix="aerobim-tz-caps-") as tmp:
            caps, _pack_id = capabilities_from_fixture_pack(pack_path, Path(tmp) / "var")
        try:
            evidence_path = pack_path.relative_to(Path(__file__).resolve().parents[4]).as_posix()
        except ValueError:
            evidence_path = pack_path.as_posix()
    payload = generate_tz_matrix_status(
        capabilities=caps,
        evidence_manifest={"customer_corpus_present": bool(args.customer_corpus)},
        evidence_path=evidence_path,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out = args.out
    if args.write_docs_evidence:
        out = (
            Path(__file__).resolve().parents[4]
            / "docs"
            / "evidence"
            / "tz-matrix-status-latest.json"
        )
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
