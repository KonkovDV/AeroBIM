"""IfcTester coverage of public jurisdiction IDS packs that are not Samolet.

Moscow AGR IDS (stroimprosto.mos.ru) and SPb GAU CGE IDS (spbexp.ru).
Does not close RT-002. No new port.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.export_moexp_ids_coverage import (
    _mapping,
    build_ids_engine_coverage,
    default_fixture_ifc,
    write_moexp_ids_coverage,
)

PACKS: dict[str, dict[str, Any]] = {
    "moscow-agr": {
        "artifact_type": "moscow_agr_ids_coverage",
        "title": "Official Moscow AGR IDS (ДГП / СтроимПросто)",
        "pack_rel": "samples/ids/moscow-agr/pack",
        "source_page": "https://stroimprosto.mos.ru/knowledge/article/cim-agr/",
        "claim_boundary": (
            "Official Moscow AGR IDS zip from stroimprosto.mos.ru (АР / БиО / ПС / МССК). "
            "IfcTester engine coverage on a wall fixture is not CIM AGR acceptance, "
            "not УКЭП, and not a Samolet-signed pack. RT-002 stays OPEN."
        ),
        "evidence_stem": "norm-pack-moscow-agr-coverage-2026-08",
        "artifacts_dir": "artifacts/norm-pack-moscow-agr",
        "allow_reason": "Official Moscow AGR IDS engine coverage; not Samolet profile",
    },
    "spbexp": {
        "artifact_type": "spbexp_ids_coverage",
        "title": "Official SPb GAU CGE IDS 1.0",
        "pack_rel": "samples/ids/spbexp/pack",
        "source_page": "https://www.spbexp.ru/bim/docs/",
        "claim_boundary": (
            "Official SPb GAU CGE IDS 1.0 zips (ЦИМ ОКС 3.1.0 + ЦИМ РИИ 1.1.0). "
            "Second public GAU jurisdiction pack. Not MosoblGosExpertiza. "
            "Not a Samolet-signed acceptance profile. RT-002 stays OPEN."
        ),
        "evidence_stem": "norm-pack-spbexp-coverage-2026-08",
        "artifacts_dir": "artifacts/norm-pack-spbexp",
        "allow_reason": "Official SPb CGE IDS engine coverage; not Samolet profile",
    },
}


def render_public_ids_coverage_markdown(
    coverage: dict[str, Any], *, title: str, allow_reason: str
) -> str:
    summary = _mapping(coverage.get("summary"))
    lines = [
        f'<!-- claims-lint: allow-file reason="{allow_reason}" -->',
        f"# {title}",
        "",
        f"**claim_level:** `{coverage.get('claim_level')}`",
        f"**customer_accuracy_not_established:** `{coverage.get('customer_accuracy_not_established')}`",
        f"**closes_rt002_customer_profile:** `{coverage.get('closes_rt002_customer_profile')}`",
        "",
        str(coverage.get("claim_boundary") or ""),
        "",
        f"Source: {coverage.get('source_page')}",
        "",
        "## Engine coverage (headline)",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| IDS files | {summary.get('ids_file_count')} |",
        f"| Specifications | {summary.get('specification_count')} |",
        f"| Executable (IfcTester ran) | {summary.get('executable')} |",
        f"| Unsupported facets | {summary.get('unsupported')} |",
        f"| Load errors | {summary.get('load_error')} |",
        "",
        "## Fixture probe (not CIM compliance)",
        "",
        "Open fixture `samples/ifc/wall-pset-qto-pass.ifc`. Fail here means the spec ran.",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Pass on fixture | {summary.get('executable_pass_on_fixture')} |",
        f"| Fail on fixture | {summary.get('executable_fail_on_fixture')} |",
        "",
        f"Generated at: `{coverage.get('generated_at')}`",
        f"content_sha256: `{coverage.get('content_sha256')}`",
        "",
    ]
    return "\n".join(lines)


def export_pack(pack_id: str, *, root: Path, ifc_path: Path) -> dict[str, Any]:
    meta = PACKS[pack_id]
    pack_dir = root / str(meta["pack_rel"])
    coverage = build_ids_engine_coverage(
        pack_dir=pack_dir,
        ifc_path=ifc_path,
        artifact_type=str(meta["artifact_type"]),
        claim_boundary=str(meta["claim_boundary"]),
        source_page=str(meta["source_page"]),
        extra_fields={
            "pack_id": pack_id,
            "samolet_alias": False,
            "customer_signed": False,
        },
    )
    evidence_stem = str(meta["evidence_stem"])
    artifacts_dir = root / str(meta["artifacts_dir"])
    evidence_json = root / "docs" / "evidence" / f"{evidence_stem}.json"
    evidence_md = root / "docs" / "evidence" / f"{evidence_stem}.md"
    write_moexp_ids_coverage(
        coverage,
        artifacts_json=artifacts_dir / "coverage.json",
        evidence_json=evidence_json,
        evidence_md=evidence_md,
    )
    evidence_md.write_text(
        render_public_ids_coverage_markdown(
            coverage,
            title=str(meta["title"]),
            allow_reason=str(meta["allow_reason"]),
        ),
        encoding="utf-8",
    )
    return coverage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=(*PACKS, "all"), default="all")
    parser.add_argument("--ifc", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    ifc_path = args.ifc or default_fixture_ifc(root)
    selected = list(PACKS) if args.pack == "all" else [args.pack]
    for pack_id in selected:
        coverage = export_pack(pack_id, root=root, ifc_path=ifc_path)
        summary = coverage.get("summary") or {}
        print(pack_id, json.dumps(summary, ensure_ascii=False))
        print("content_sha256", coverage.get("content_sha256"))
        if coverage.get("closes_rt002_customer_profile"):
            raise SystemExit("honesty lock: public pack must not close RT-002")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
