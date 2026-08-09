#!/usr/bin/env python3
"""Fail CI when a deferred control's activates_on date has passed (waiver registry)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path


def _parse_day(raw: str) -> date:
    text = raw.strip()
    if "T" in text:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC).date()
    return date.fromisoformat(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "governance/deferred_controls_registry.json",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Override UTC date YYYY-MM-DD (tests only)",
    )
    args = parser.parse_args()
    if not args.registry.is_file():
        print(f"ERROR: registry missing: {args.registry}", file=sys.stderr)
        return 1
    payload = json.loads(args.registry.read_text(encoding="utf-8"))
    today = date.fromisoformat(args.today) if args.today else datetime.now(tz=UTC).date()
    waivers = payload.get("waivers") or []
    overdue: list[str] = []
    for item in waivers:
        if not isinstance(item, dict):
            continue
        if str(item.get("state") or "").lower() != "deferred":
            continue
        activates = str(item.get("activates_on") or "").strip()
        if not activates:
            overdue.append(f"{item.get('id')}: deferred without activates_on")
            continue
        if today >= _parse_day(activates):
            overdue.append(
                f"{item.get('id')}: deferred past activates_on={activates} (today={today.isoformat()})"
            )
    print(f"deferred_controls checked={len(waivers)} overdue={len(overdue)} today={today.isoformat()}")
    for line in overdue:
        print(f"ERROR: {line}", file=sys.stderr)
    return 1 if overdue else 0


if __name__ == "__main__":
    raise SystemExit(main())
