"""Assemble the KT#3 pack that does not wait for Samolet files."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.kt3_without_customer import (
    OWNER_DECISION_DATE,
    assemble_kt3_without_customer,
    render_markdown,
)
from aerobim.tools.benchmark_project_package import repo_root


def build_payload(repo: Path, *, generated_at: str | None = None) -> dict[str, Any]:
    stamp = generated_at or datetime.now(tz=UTC).isoformat()
    return assemble_kt3_without_customer(repo, generated_at=stamp)


def write_payload(
    payload: dict[str, Any],
    *,
    artifacts_json: Path,
    artifacts_md: Path | None = None,
) -> None:
    artifacts_json.parent.mkdir(parents=True, exist_ok=True)
    artifacts_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if artifacts_md is not None:
        artifacts_md.parent.mkdir(parents=True, exist_ok=True)
        artifacts_md.write_text(render_markdown(payload), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="KT#3 pack without Samolet files. Re-scope. Checkpoint stays NO_GO."
    )
    parser.add_argument(
        "--write-docs-evidence",
        action="store_true",
        help="Also write docs/evidence (default: artifacts/ only).",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Override timestamp (tests / frozen pin).",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_payload(root, generated_at=args.generated_at)
    write_payload(
        payload,
        artifacts_json=root / "artifacts" / "kt3-without-customer" / "latest.json",
        artifacts_md=root / "artifacts" / "kt3-without-customer" / "latest.md",
    )
    if args.write_docs_evidence:
        write_payload(
            payload,
            artifacts_json=root / "docs" / "evidence" / "kt3-without-customer-latest.json",
            artifacts_md=root / "docs" / "evidence" / "kt3-without-customer-2026-08.md",
        )
    print(
        json.dumps(
            {
                "checkpoint": payload["checkpoint"],
                "plan_b_decision": payload["plan_b_decision"],
                "owner_decision_date": payload.get("owner_decision_date", OWNER_DECISION_DATE),
                "closes_rt001": payload["closes_rt001"],
                "closes_rt002": payload["closes_rt002"],
                "closes_rt003": payload["closes_rt003"],
                "customer_files_expected": payload["customer_files_expected"],
                "waiting_for_customer": payload["waiting_for_customer"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
