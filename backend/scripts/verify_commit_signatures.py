#!/usr/bin/env python3
"""Commit-signature governance gate (RT-GOV-003 / Wave 5)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_policy(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {
            "enforce_ci": False,
            "min_signed_ratio": 0.0,
            "ratchet_target_ratio": 0.5,
            "ratchet_effective_date": "2026-09-01",
            "inspect_depth": 30,
            "require_head_signed_on_release_tags": False,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _signed_commits(depth: int) -> tuple[int, int, list[str]]:
    log = subprocess.check_output(
        ["git", "log", f"-{depth}", "--pretty=format:%G?"],
        text=True,
    )
    marks = [line.strip() for line in log.splitlines() if line.strip()]
    signed = sum(1 for mark in marks if mark == "G")
    return signed, len(marks), marks


def _head_is_signed() -> bool:
    mark = subprocess.check_output(
        ["git", "log", "-1", "--pretty=format:%G?"],
        text=True,
    ).strip()
    return mark == "G"


def _on_release_tag() -> bool:
    try:
        describe = subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return False
    return bool(describe)


def _effective_min_ratio(policy: dict[str, object]) -> float:
    base = float(policy.get("min_signed_ratio", 0.0) or 0.0)
    target = float(policy.get("ratchet_target_ratio", 0.0) or 0.0)
    effective_raw = (policy.get("ratchet_effective_date") or "").strip()
    if not effective_raw:
        return base
    try:
        effective = datetime.fromisoformat(effective_raw).replace(tzinfo=UTC)
    except ValueError:
        return base
    if datetime.now(tz=UTC) >= effective:
        return max(base, target)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=_repo_root() / "governance/commit_signing_policy.json")
    parser.add_argument("--depth", type=int, default=None)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    depth = int(args.depth or policy.get("inspect_depth") or 30)
    signed, total, _marks = _signed_commits(depth)
    ratio = (signed / total) if total else 0.0
    min_ratio = _effective_min_ratio(policy)
    enforce = bool(policy.get("enforce_ci", False))

    print(f"signed_commits={signed}/{total} ratio={ratio:.2f} required_min_ratio={min_ratio:.2f}")

    if signed == 0:
        print(
            "NOTE: no GPG-signed commits in window; enable git commit.gpgsign and upload pubkey",
        )

    if enforce and ratio < min_ratio:
        print(
            f"ERROR: signed ratio {ratio:.2f} below required {min_ratio:.2f}",
            file=sys.stderr,
        )
        return 1

    if enforce and bool(policy.get("require_head_signed_on_release_tags")) and _on_release_tag():
        if not _head_is_signed():
            print("ERROR: release tag HEAD must be GPG-signed", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
