#!/usr/bin/env python3
"""Flip A4 signing enforcement on/after 2026-08-11 (registry + policy together).

Run from repo root after green CI dry-run::

    python scripts/activate_a4_signing_enforcement.py
    # then commit signed with B5690EEEBB952194

Before the calendar date, refuse unless ``--force`` (escape hatch only).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_POLICY = _REPO / "governance" / "commit_signing_policy.json"
_REGISTRY = _REPO / "governance" / "deferred_controls_registry.json"
_ACTIVATES = date(2026, 8, 11)
_FLAGS = ("enforce_ci", "fail_on_unverifiable_signature")
_WAIVER_ID = "A4-signing-enforcement"


def _today(raw: str | None) -> date:
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(tz=UTC).date()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", default=None, help="Override UTC date YYYY-MM-DD")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow flip before activates_on (not for production calendar)",
    )
    args = parser.parse_args()
    today = _today(args.today)
    if today < _ACTIVATES and not args.force:
        print(
            f"ERROR: A4 activates_on={_ACTIVATES.isoformat()}; today={today.isoformat()}. "
            "Re-run on/after that date, or pass --force for a dry local experiment.",
            file=sys.stderr,
        )
        return 2

    policy = json.loads(_POLICY.read_text(encoding="utf-8"))
    for flag in _FLAGS:
        policy[flag] = True
    if float(policy.get("min_signed_ratio") or 0) < float(policy.get("ratchet_target_ratio") or 0):
        policy["min_signed_ratio"] = policy["ratchet_target_ratio"]
    _POLICY.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    registry = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    found = False
    for item in registry.get("waivers") or []:
        if isinstance(item, dict) and item.get("id") == _WAIVER_ID:
            item["state"] = "active"
            found = True
            break
    if not found:
        print(f"ERROR: waiver {_WAIVER_ID} missing from registry", file=sys.stderr)
        return 1
    _REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"A4 flipped: policy flags {_FLAGS}=true; registry {_WAIVER_ID} state=active; "
        f"today={today.isoformat()}"
    )
    print("Commit with B5690EEEBB952194 and push; verify deferred_controls + signing jobs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
