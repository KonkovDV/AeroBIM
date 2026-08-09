#!/usr/bin/env python3
"""Commit-signature governance gate (RT-GOV-003 / Wave 5 / N-56).

Trust is anchored in ``governance/trusted_signing_keys/*.asc``, not in the
runner keyring ownertrust. A cryptographically valid signature (git ``G`` or
``U``) counts toward the ratio only when its fingerprint matches a trusted
key file. Everything else with a signature is unverifiable (exit 2 when
enforced) — including ``U`` from an unknown key and ``E`` (missing key).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _gpg_bin() -> str:
    return os.environ.get("AEROBIM_GPG_BIN") or os.environ.get("GPG") or "gpg"


def _load_policy(path: Path) -> dict[str, object]:
    if not path.is_file():
        print(f"ERROR: policy file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprints_from_asc(keys_dir: Path) -> set[str]:
    """Read primary fingerprints from ASCII-armored public keys (repo anchor)."""

    gpg = _gpg_bin()
    found: set[str] = set()
    for path in sorted(keys_dir.glob("*.asc")):
        proc = subprocess.run(
            [gpg, "--show-keys", "--with-colons", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            print(f"ERROR: cannot read trusted key {path.name}", file=sys.stderr)
            raise SystemExit(1)
        for line in proc.stdout.splitlines():
            if line.startswith("fpr:"):
                parts = line.split(":")
                if len(parts) > 9 and parts[9]:
                    found.add(parts[9].upper())
    return found


def _normalize_fpr(raw: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", raw or "").upper()


def _commit_sig_rows(depth: int) -> list[tuple[str, str]]:
    """Return [(status, fingerprint), ...] for the last ``depth`` commits."""

    log = subprocess.check_output(
        ["git", "log", f"-{depth}", "--pretty=format:%G? %GF"],
        text=True,
    )
    rows: list[tuple[str, str]] = []
    for line in log.splitlines():
        text = line.strip()
        if not text:
            continue
        parts = text.split(None, 1)
        status = parts[0]
        fpr = _normalize_fpr(parts[1] if len(parts) > 1 else "")
        rows.append((status, fpr))
    return rows


def _classify(
    rows: list[tuple[str, str]],
    trusted: set[str],
) -> tuple[int, int, int, int]:
    """Return (trusted_signed, unverifiable, other_bad, total).

    trusted_signed: G/U whose fingerprint is in the repo key set (N-56).
    unverifiable: E, or G/U with missing/foreign fingerprint.
    other_bad: B/X/Y/R.
    """

    signed = 0
    unverifiable = 0
    other_bad = 0
    for status, fpr in rows:
        if status == "N":
            continue
        if status in {"B", "X", "Y", "R"}:
            other_bad += 1
            continue
        if status == "E":
            unverifiable += 1
            continue
        if status in {"G", "U"}:
            if fpr and fpr in trusted:
                signed += 1
            else:
                unverifiable += 1
            continue
        unverifiable += 1
    return signed, unverifiable, other_bad, len(rows)


def _head_trusted(trusted: set[str]) -> bool:
    rows = _commit_sig_rows(1)
    if not rows:
        return False
    signed, _, _, _ = _classify(rows, trusted)
    return signed == 1


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
    parser.add_argument(
        "--keys-dir",
        type=Path,
        default=None,
        help="Override trusted ASC directory (default: policy trusted_keys_dir)",
    )
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    depth = int(args.depth or policy.get("inspect_depth") or 50)
    scope = str(policy.get("ratio_scope") or "inspect_window")
    if scope not in {"inspect_window", "last_n_commits"}:
        print(
            f"ERROR: ratio_scope={scope!r} rejected; use inspect_window "
            "(full-history ratios are unreachable after unsigned bulk history — N-53)",
            file=sys.stderr,
        )
        return 1

    keys_dir = args.keys_dir
    if keys_dir is None:
        rel = str(policy.get("trusted_keys_dir") or "governance/trusted_signing_keys")
        keys_dir = _repo_root() / rel
    if not keys_dir.is_dir():
        print(f"ERROR: trusted keys dir missing: {keys_dir}", file=sys.stderr)
        return 1
    trusted = _fingerprints_from_asc(keys_dir)
    if not trusted:
        print(f"ERROR: no fingerprints in {keys_dir}", file=sys.stderr)
        return 1

    rows = _commit_sig_rows(depth)
    signed, unverifiable, other_bad, total = _classify(rows, trusted)
    ratio = (signed / total) if total else 0.0
    min_ratio = _effective_min_ratio(policy)
    enforce = bool(policy.get("enforce_ci", False))
    fail_unverifiable = bool(policy.get("fail_on_unverifiable_signature", enforce))

    # N-55: warn when trusted signatures sit near the trailing edge of the window.
    trailing_unsigned = 0
    for status, fpr in reversed(rows):
        if status in {"G", "U"} and fpr in trusted:
            break
        trailing_unsigned += 1
    print(
        f"signed_trusted={signed}/{total} ratio={ratio:.2f} "
        f"window=last_{depth} scope={scope} "
        f"unverifiable={unverifiable} bad={other_bad} "
        f"trusted_keys={len(trusted)} "
        f"required_min_ratio={min_ratio:.2f}"
    )
    if trailing_unsigned and signed:
        print(
            f"NOTE: N-55 window drift risk — {trailing_unsigned} commit(s) after the "
            "newest trusted signature; unsigned commits push signed merges out of the window"
        )

    if signed == 0:
        print(
            "NOTE: no trusted-key signatures in window; enable commit signing and keep "
            "public keys in governance/trusted_signing_keys",
        )
    if unverifiable:
        print(
            f"NOTE: {unverifiable} commit(s) have unverifiable signatures "
            "(missing key, or fingerprint not in trusted_signing_keys)",
        )

    if fail_unverifiable and (unverifiable > 0 or other_bad > 0):
        print(
            "ERROR: unverifiable or bad commit signatures present "
            f"(unverifiable={unverifiable}, bad={other_bad}); "
            "only G/U with a fingerprint in trusted_signing_keys counts",
            file=sys.stderr,
        )
        return 2

    if enforce and ratio < min_ratio:
        print(
            f"ERROR: signed ratio {ratio:.2f} below required {min_ratio:.2f} "
            f"(trusted fingerprints only, window last {depth})",
            file=sys.stderr,
        )
        return 1

    if enforce and bool(policy.get("require_head_signed_on_release_tags")) and _on_release_tag():
        if not _head_trusted(trusted):
            print(
                "ERROR: release tag HEAD must be signed by a trusted_signing_keys fingerprint",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
