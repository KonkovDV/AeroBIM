#!/usr/bin/env python3
"""Fail if allowlisted live ``*latest.json`` artifacts are missing or older than 7 days.

Frozen benches (AECV, IFC-Bench, dated SLA pins) stay off this list. Not a
customer freshness SLA. Checkpoint GO; customer_go false.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "docs" / "evidence"

MAX_AGE_DAYS = 7
LIVE_LATEST_JSON: tuple[str, ...] = (
    "weekly-eng-status-latest.json",
    "tz-matrix-status-latest.json",
    "defect-injection-recall-run-latest.json",
    "sla-package-scale-latest.json",
    "data-residency-inventory-latest.json",
    "substitution-matrix-latest.json",
)


def parse_generated_at(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def check_file(
    path: Path,
    *,
    now: datetime,
    max_age: timedelta,
) -> str | None:
    if not path.is_file():
        return f"missing {path.as_posix()}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"unreadable {path.as_posix()}: {exc}"
    if not isinstance(payload, dict):
        return f"{path.as_posix()} is not a JSON object"
    generated = parse_generated_at(payload.get("generated_at"))
    if generated is None:
        return f"{path.as_posix()} missing generated_at"
    age = now - generated
    if age > max_age:
        return (
            f"{path.as_posix()} generated_at {generated.isoformat()} "
            f"is {age.days}d old (max {max_age.days}d)"
        )
    if age < timedelta(0):
        return f"{path.as_posix()} generated_at is in the future"
    return None


def collect_errors(
    evidence_dir: Path,
    names: tuple[str, ...] = LIVE_LATEST_JSON,
    *,
    now: datetime | None = None,
    max_age_days: int = MAX_AGE_DAYS,
) -> list[str]:
    clock = now or datetime.now(tz=UTC)
    max_age = timedelta(days=max_age_days)
    errors: list[str] = []
    for name in names:
        err = check_file(evidence_dir / name, now=clock, max_age=max_age)
        if err:
            errors.append(err)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--max-age-days", type=int, default=MAX_AGE_DAYS)
    args = parser.parse_args(argv)
    errors = collect_errors(
        args.evidence_dir,
        now=datetime.now(tz=UTC),
        max_age_days=args.max_age_days,
    )
    if errors:
        print("live evidence freshness FAIL:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "PASS",
                "checked": list(LIVE_LATEST_JSON),
                "max_age_days": args.max_age_days,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
