"""Export the RT-001/002/003 measurement-vs-residual volume snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.rt_blocker_volumes import assemble_rt_blocker_volumes
from aerobim.tools.benchmark_project_package import repo_root


def build_payload(repo: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    payload = assemble_rt_blocker_volumes(repo)
    payload["generated_at"] = generated_at or datetime.now(tz=UTC).isoformat()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="RT blocker volumes: substitutes close measurement; residuals stay open."
    )
    parser.add_argument(
        "--write-docs-evidence",
        action="store_true",
        help="Write docs/evidence/rt-blocker-volumes-latest.json (default: artifacts/ only).",
    )
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_payload(root, generated_at=args.generated_at)
    out = root / "artifacts" / "rt-blocker-volumes" / "latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    if args.write_docs_evidence:
        docs = root / "docs" / "evidence" / "rt-blocker-volumes-latest.json"
        docs.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "checkpoint": payload["checkpoint"],
                "closes_rt001": payload["closes_rt001"],
                "closes_rt002": payload["closes_rt002"],
                "closes_rt003": payload["closes_rt003"],
                "RT-001": {
                    "a": payload["RT-001"]["a_content_pairing"],
                    "b1_protocol": payload["RT-001"]["b1_protocol_rehearsal"],
                    "b2_humans": payload["RT-001"]["b2_criterion_dual_rater"],
                },
                "RT-002": {
                    "a": payload["RT-002"]["a_regulatory"],
                    "b_eir": payload["RT-002"]["b_eir_carrier"],
                    "c_signed": payload["RT-002"]["c_corporate_signed"],
                },
                "RT-003": {
                    "a": payload["RT-003"]["a_federated_geometric_rehearsal"],
                    "b1_navis": payload["RT-003"]["b1_navis_federation_carrier"],
                    "b2_graph": payload["RT-003"]["b2_ifc_system_graph_rehearsal"],
                    "b3_mep": payload["RT-003"]["b3_mep_system_clash"],
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
