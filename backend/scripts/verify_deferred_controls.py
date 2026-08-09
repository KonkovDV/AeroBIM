#!/usr/bin/env python3
"""Fail CI when deferred controls expire — and when registry state disagrees with mechanism (N-58)."""

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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=_repo_root() / "governance/deferred_controls_registry.json",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=_repo_root() / "governance/commit_signing_policy.json",
        help="Mechanism file read when waivers list policy_flags (N-58)",
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
    errors: list[str] = []
    policy: dict[str, object] | None = None
    if args.policy.is_file():
        policy = json.loads(args.policy.read_text(encoding="utf-8"))

    for item in waivers:
        if not isinstance(item, dict):
            continue
        wid = str(item.get("id") or "?")
        state = str(item.get("state") or "").lower()
        flags = [str(f) for f in (item.get("policy_flags") or [])]
        activates = str(item.get("activates_on") or "").strip()

        if flags:
            if policy is None:
                errors.append(f"{wid}: policy_flags set but policy file missing: {args.policy}")
            else:
                actual = {flag: bool(policy.get(flag)) for flag in flags}
                if state == "active":
                    for flag, value in actual.items():
                        if not value:
                            errors.append(
                                f"{wid}: state=active but {flag}=false in {args.policy.name} (N-58)"
                            )
                elif state == "deferred":
                    for flag, value in actual.items():
                        if value:
                            errors.append(
                                f"{wid}: state=deferred but {flag}=true in {args.policy.name} "
                                "(control escaped the registry — N-58)"
                            )
                    print(
                        f"NOTE: {wid} deferred flags={flags} "
                        f"must flip together on {activates}; actual={actual}"
                    )

        numeric = item.get("policy_numeric")
        if isinstance(numeric, dict):
            rel = str(numeric.get("file") or "").strip()
            field = str(numeric.get("field") or "").strip()
            target: Path | None = None
            if rel:
                candidate = Path(rel)
                target = candidate if candidate.is_file() else _repo_root() / rel
            if not field or target is None or not target.is_file():
                errors.append(f"{wid}: policy_numeric missing file/field or file absent")
            else:
                mech = json.loads(target.read_text(encoding="utf-8"))
                got = mech.get(field)
                expect = (
                    numeric.get("when_active")
                    if state == "active"
                    else numeric.get("when_deferred")
                )
                if expect is not None and got != expect:
                    errors.append(
                        f"{wid}: {rel} {field}={got!r} expected {expect!r} for state={state} (N-43)"
                    )
                else:
                    print(f"NOTE: {wid} {field}={got} state={state} (ok)")

        if state != "deferred":
            continue
        if not activates:
            errors.append(f"{wid}: deferred without activates_on")
            continue
        if today >= _parse_day(activates):
            flag_note = ""
            if flags:
                flag_note = f"; enable policy flags {flags} and set state=active"
            errors.append(
                f"{wid}: deferred past activates_on={activates} "
                f"(today={today.isoformat()}){flag_note}"
            )

    print(
        f"deferred_controls checked={len(waivers)} errors={len(errors)} today={today.isoformat()}"
    )
    for line in errors:
        print(f"ERROR: {line}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
