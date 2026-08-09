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
        print(f"ERROR: policy file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _signed_commits(depth: int) -> tuple[int, int, int, int, list[str]]:
    """Return (good_signed, unverifiable_E, other_bad, total, marks).

    Only ``G`` (good trusted signature) counts toward the signed ratio.
    ``E`` (cannot check) is worse than unsigned and must not inflate the ratio.
    """

    log = subprocess.check_output(
        ["git", "log", f"-{depth}", "--pretty=format:%G?"],
        text=True,
    )
    marks = [line.strip() for line in log.splitlines() if line.strip()]
    signed = sum(1 for mark in marks if mark == "G")
    unverifiable = sum(1 for mark in marks if mark == "E")
    other_bad = sum(1 for mark in marks if mark in {"B", "U", "X", "Y", "R"})
    return signed, unverifiable, other_bad, len(marks), marks


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
    parser.add_argument(
        "--policy",
        type=Path,
        default=_repo_root() / "governance/commit_signing_policy.json",
    )
    parser.add_argument("--depth", type=int, default=None)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    depth = int(args.depth or policy.get("inspect_depth") or 30)
    signed, unverifiable, other_bad, total, _marks = _signed_commits(depth)
    ratio = (signed / total) if total else 0.0
    min_ratio = _effective_min_ratio(policy)
    enforce = bool(policy.get("enforce_ci", False))
    # Distinct from unsigned: E/B/U/... fail enforcement even if ratio is met.
    fail_unverifiable = bool(policy.get("fail_on_unverifiable_signature", enforce))

    print(
        f"signed_commits_G={signed}/{total} ratio={ratio:.2f} "
        f"unverifiable_E={unverifiable} bad={other_bad} "
        f"required_min_ratio={min_ratio:.2f}"
    )

    if signed == 0:
        print(
            "NOTE: no G-status signed commits in window; enable git commit.gpgsign and upload pubkey",
        )
    if unverifiable:
        print(
            f"NOTE: {unverifiable} commit(s) have unverifiable signatures (git %G?=E); "
            "these do not count as signed and must not be treated as unsigned-equivalent",
        )

    if fail_unverifiable and (unverifiable > 0 or other_bad > 0):
        print(
            "ERROR: unverifiable or bad commit signatures present "
            f"(E={unverifiable}, bad={other_bad}); only G-status with a trusted key counts",
            file=sys.stderr,
        )
        return 2

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
