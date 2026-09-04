"""Write the RT-001 dual-rater protocol rehearsal CSV and evidence pin."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.rt001_dual_rater_simulation import (
    CSV_REL,
    EVIDENCE_JSON_REL,
    EVIDENCE_MD_REL,
    assemble_rt001_dual_rater_simulation,
    csv_records,
    rehearsal_units,
    render_adjudication_csv,
    render_evidence_markdown,
)
from aerobim.tools.benchmark_project_package import repo_root
from aerobim.tools.measure_adjudicator_agreement import measure_adjudication_csv


def build_payload(repo: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    payload = assemble_rt001_dual_rater_simulation(repo)
    payload["generated_at"] = generated_at or datetime.now(tz=UTC).isoformat()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulate two independent rater passes on the fixture pack. Not humans."
    )
    parser.add_argument("--generated-at", default=None)
    parser.add_argument(
        "--write-docs-evidence",
        action="store_true",
        help="Write CSV + docs/evidence pin (default: artifacts/ only).",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_payload(root, generated_at=args.generated_at)
    csv_text = render_adjudication_csv(csv_records(rehearsal_units(root)))
    artifacts = root / "artifacts" / "rt001-dual-rater-simulation"
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / "latest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (artifacts / "latest.csv").write_text(csv_text, encoding="utf-8")
    if args.write_docs_evidence:
        csv_path = root / CSV_REL
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(csv_text, encoding="utf-8")
        json_path = root / EVIDENCE_JSON_REL
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        md_path = root / EVIDENCE_MD_REL
        md_path.write_text(render_evidence_markdown(payload), encoding="utf-8")
        tool_metrics = measure_adjudication_csv(csv_path)
        payload["tool_csv_cohens_kappa"] = tool_metrics["cohens_kappa"]
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "checkpoint": payload["checkpoint"],
                "closes_rt001": payload["closes_rt001"],
                "independent_human_raters": payload["independent_human_raters"],
                "n": payload["n"],
                "cohens_kappa": payload["cohens_kappa"],
                "krippendorff_alpha": payload["krippendorff_alpha"],
                "gwet_ac1": payload["gwet_ac1"],
                "b_protocol_rehearsal": payload["b_protocol_rehearsal"],
                "b_criterion_dual_rater": payload["b_criterion_dual_rater"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
