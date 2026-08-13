"""Kimi vs Qwen stamp/title-block comparison contour.

Advisory-only. Never sets summary.passed. Without AEROBIM_LLM_API_KEY the run is
SKIPPED — no invented scores. Needed for tracker 14.08 honesty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root

CLAIM_BOUNDARY = (
    "VLM advisory on stamp/title-block crop only. fixture_only. "
    "Not door/window counting. Not product accuracy. Invalid JSON → fail-closed skip."
)


def build_vlm_comparison(*, api_key_present: bool) -> dict[str, Any]:
    status = "RUNNABLE" if api_key_present else "SKIPPED"
    reason = None if api_key_present else "AEROBIM_LLM_API_KEY not set — refuse to invent metrics"
    payload: dict[str, Any] = {
        "artifact_type": "vlm_stamp_comparison",
        "schema_version": "1.0.0",
        "claim_level": "fixture_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "scenario": "stamp_title_block_explication",
        "not_in_scope": ["door_count", "window_count", "whole_sheet_geometry"],
        "models": [
            {
                "id": "qwen3-vl",
                "route": "Yandex AI Studio allowlisted host",
                "role": "primary_candidate",
            },
            {
                "id": "kimi",
                "route": "refused on Yandex host (kimi-k3 default gate)",
                "role": "comparison_only_if_non_yandex_allowlisted",
            },
        ],
        "status": status,
        "skip_reason": reason,
        "metrics": None,
        "recommendation": (
            "No live scores this run. Do not pick a model from empty metrics. "
            "Re-run 17.08 with Studio key; schema-invalid output = zero score / skip."
        ),
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "customer_accuracy_not_established": True,
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    root = repo_root()
    payload = build_vlm_comparison(api_key_present=bool((os.getenv("AEROBIM_LLM_API_KEY") or "").strip()))
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifacts = args.output or (root / "artifacts" / "vlm-comparison.json")
    evidence = root / "docs" / "evidence" / "vlm-comparison-2026-08.json"
    artifacts.parent.mkdir(parents=True, exist_ok=True)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    artifacts.write_text(text, encoding="utf-8")
    evidence.write_text(text, encoding="utf-8")
    md = root / "docs" / "evidence" / "vlm-comparison-2026-08.md"
    md.write_text(
        "\n".join(
            [
                "# VLM stamp comparison (tracker 2.2)",
                "",
                f"**status:** `{payload['status']}`",
                f"**claim_level:** `{payload['claim_level']}`",
                "",
                payload["claim_boundary"],
                "",
                payload.get("skip_reason") or payload["recommendation"],
                "",
                f"content_sha256: `{payload['content_sha256']}`",
                f"generated_at: `{payload['generated_at']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
