#!/usr/bin/env python3
"""Commit-signature governance gate (RT-GOV-003 / N-53..N-56 / N-59).

Trust is anchored in ``governance/trusted_signing_keys/*.asc`` (author keys).
Optional ``.../platform/*.asc`` (e.g. GitHub web-flow) verify without counting
toward the signed ratio — platform confirmation, not authorship.

Classification of a cryptographically valid signature whose fingerprint is
**not** in either set: **unverifiable** (same bucket as ``E``). With
``fail_on_unverifiable_signature`` that is exit 2 — worse than unsigned.

N-59: commits *after* ``n59_enforced_after`` that touch the author/platform
key directory must be signed by an already-listed author fingerprint. The
cutoff exists because ``git filter-repo`` strips signatures; rewritten
history cannot satisfy a path+signature check.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _gpg_bin() -> str:
    env = os.environ.get("AEROBIM_GPG_BIN") or os.environ.get("GPG")
    if env:
        return env
    try:
        proc = subprocess.run(
            ["git", "config", "--get", "gpg.program"],
            text=True,
            capture_output=True,
            check=False,
        )
        configured = (proc.stdout or "").strip()
        if configured:
            return configured
    except OSError:
        pass
    return "gpg"


def _load_policy(path: Path) -> dict[str, object]:
    if not path.is_file():
        print(f"ERROR: policy file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprints_from_asc_files(paths: list[Path]) -> set[str]:
    gpg = _gpg_bin()
    found: set[str] = set()
    for path in paths:
        proc = subprocess.run(
            [gpg, "--show-keys", "--with-colons", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            print(f"ERROR: cannot read key {path}", file=sys.stderr)
            raise SystemExit(1)
        for line in proc.stdout.splitlines():
            if line.startswith("fpr:"):
                parts = line.split(":")
                if len(parts) > 9 and parts[9]:
                    found.add(parts[9].upper())
    return found


def _normalize_fpr(raw: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", raw or "").upper()


def _commit_sig_rows(depth: int) -> list[tuple[str, str, str, str]]:
    """Return [(status, fingerprint, short_sha, subject), ...] newest first."""

    # NUL fields: unsigned commits have empty %GF, and whitespace split would
    # treat the short SHA as the fingerprint and the subject as the SHA.
    log = subprocess.check_output(
        ["git", "log", f"-{depth}", "--pretty=format:%G?%x00%GF%x00%h%x00%s"],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    rows: list[tuple[str, str, str, str]] = []
    for line in log.splitlines():
        text = line.strip("\r")
        if not text:
            continue
        parts = text.split("\0", 3)
        status = parts[0] if parts else ""
        fpr = _normalize_fpr(parts[1] if len(parts) > 1 else "")
        short = parts[2] if len(parts) > 2 else ""
        subject = parts[3] if len(parts) > 3 else ""
        rows.append((status, fpr, short, subject))
    return rows


def _classify(
    rows: list[tuple[str, str, str, str]],
    author_trusted: set[str],
    platform_trusted: set[str],
) -> tuple[int, int, int, int, list[tuple[str, str]]]:
    """Return (author_signed, unverifiable, other_bad, total, named_author_signed).

    author_signed: G/U with author-key fingerprint (counts toward ratio).
    platform G/U: verified, not counted, not unverifiable.
    foreign G/U or E: unverifiable (exit 2 when fail_on_unverifiable).
    """

    signed = 0
    unverifiable = 0
    other_bad = 0
    named: list[tuple[str, str]] = []
    for status, fpr, short, subject in rows:
        if status == "N":
            continue
        if status in {"B", "X", "Y", "R"}:
            other_bad += 1
            continue
        if status == "E":
            unverifiable += 1
            continue
        if status in {"G", "U"}:
            if fpr and fpr in author_trusted:
                signed += 1
                named.append((short, subject))
            elif fpr and fpr in platform_trusted:
                continue
            else:
                unverifiable += 1
            continue
        unverifiable += 1
    return signed, unverifiable, other_bad, len(rows), named


def _needed_signed(min_ratio: float, depth: int) -> int:
    if depth <= 0 or min_ratio <= 0:
        return 0
    return int(math.ceil(min_ratio * depth - 1e-12))


def _commits_until_ratio_break(
    rows: list[tuple[str, str, str, str]],
    author_trusted: set[str],
    *,
    min_ratio: float,
    depth: int,
) -> int | None:
    """How many new tip commits until author-signed count would fall below min_ratio.

    Critical signature = the ``needed``-th newest author-trusted commit (not the
    newest). When that one slides out of the window, the ratio breaks.
    """

    needed = _needed_signed(min_ratio, depth)
    if needed <= 0:
        return None
    positions = [
        idx
        for idx, (status, fpr, _short, _subject) in enumerate(rows)
        if status in {"G", "U"} and fpr in author_trusted
    ]
    if len(positions) < needed:
        return 0
    critical = positions[needed - 1]
    # When k new commits are prepended, index becomes critical+k; leaves at >= depth.
    return max(0, depth - critical)


def _head_trusted(author_trusted: set[str]) -> bool:
    rows = _commit_sig_rows(1)
    if not rows:
        return False
    signed, _, _, _, _ = _classify(rows, author_trusted, set())
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


def _normalize_repo_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _touches_trusted_keys_dir(paths: list[str], keys_rel: str) -> bool:
    prefix = _normalize_repo_path(keys_rel)
    if not prefix:
        return False
    for raw in paths:
        candidate = _normalize_repo_path(raw)
        if candidate == prefix or candidate.startswith(prefix + "/"):
            return True
    return False


def _is_author_trusted_sig(status: str, fpr: str, author_trusted: set[str]) -> bool:
    return status in {"G", "U"} and bool(fpr) and fpr in author_trusted


def _rev_parse_commit(rev: str) -> str | None:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def _is_exclusive_descendant(cutoff: str, commit: str) -> bool | None:
    """True if ``commit`` is a descendant of ``cutoff`` (excluding equality).

    ``None`` means the cutoff revision is missing (shallow clone / rewritten
    history). Callers then enforce N-59 on the whole inspect window.
    """

    cutoff_full = _rev_parse_commit(cutoff)
    commit_full = _rev_parse_commit(commit)
    if not cutoff_full:
        return None
    if not commit_full:
        return False
    if cutoff_full == commit_full:
        return False
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", cutoff_full, commit_full],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _commit_paths(short_sha: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", short_sha],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [_normalize_repo_path(line) for line in output.splitlines() if line.strip()]


def _n59_unsigned_key_dir_commits(
    rows: list[tuple[str, str, str, str]],
    author_trusted: set[str],
    *,
    keys_rel: str,
    cutoff: str,
) -> list[str]:
    """Short SHAs that change the key dir after the cutoff without an author signature."""

    violations: list[str] = []
    for status, fpr, short, _subject in rows:
        if not short:
            continue
        after = _is_exclusive_descendant(cutoff, short) if cutoff else None
        if after is False:
            continue
        if not _touches_trusted_keys_dir(_commit_paths(short), keys_rel):
            continue
        if _is_author_trusted_sig(status, fpr, author_trusted):
            continue
        violations.append(short)
    return violations


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
        help="Author trusted ASC directory (non-recursive *.asc)",
    )
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    depth = int(args.depth or policy.get("inspect_depth") or 50)
    scope = str(policy.get("ratio_scope") or "inspect_window")
    if scope not in {"inspect_window", "last_n_commits"}:
        print(
            f"ERROR: ratio_scope={scope!r} rejected; use inspect_window",
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

    author_files = sorted(keys_dir.glob("*.asc"))
    platform_files = sorted((keys_dir / "platform").glob("*.asc")) if (keys_dir / "platform").is_dir() else []
    author_trusted = _fingerprints_from_asc_files(author_files)
    platform_trusted = _fingerprints_from_asc_files(platform_files)
    if not author_trusted:
        print(f"ERROR: no author fingerprints in {keys_dir}/*.asc", file=sys.stderr)
        return 1

    rows = _commit_sig_rows(depth)
    if len(rows) < depth:
        print(
            f"ERROR: available history {len(rows)} < inspect_depth {depth} "
            "(shallow checkout collapses the signing window — refuse, do not decorate)",
            file=sys.stderr,
        )
        return 3

    signed, unverifiable, other_bad, total, named = _classify(
        rows, author_trusted, platform_trusted
    )
    ratio = (signed / total) if total else 0.0
    min_ratio = _effective_min_ratio(policy)
    enforce = bool(policy.get("enforce_ci", False))
    fail_unverifiable = bool(policy.get("fail_on_unverifiable_signature", enforce))
    # Countdown uses the ratio that will bind under enforcement (ratchet), not today's 0.0.
    planning_ratio = max(min_ratio, float(policy.get("ratchet_target_ratio", 0.0) or 0.0))
    needed = _needed_signed(planning_ratio, depth)
    until_break = _commits_until_ratio_break(
        rows, author_trusted, min_ratio=planning_ratio, depth=depth
    )

    print(
        f"signed_trusted={signed}/{total} ratio={ratio:.2f} "
        f"window=last_{depth} scope={scope} "
        f"unverifiable={unverifiable} bad={other_bad} "
        f"author_keys={len(author_trusted)} platform_keys={len(platform_trusted)} "
        f"required_min_ratio={min_ratio:.2f} planning_ratio={planning_ratio:.2f} "
        f"needed_signed={needed}"
    )
    for short, subject in named:
        print(f"trusted_commit {short} {subject}")
    if until_break is not None and needed > 0:
        print(
            f"commits_until_ratio_break={until_break} "
            f"(break when author-trusted falls below {needed}/{depth} at planning_ratio={planning_ratio:.2f})"
        )

    if signed == 0:
        print(
            "NOTE: no author-trusted signatures in window; sign with a key whose "
            ".asc is already in trusted_signing_keys (or add the .asc in the same commit)"
        )
    if unverifiable:
        print(
            f"NOTE: {unverifiable} commit(s) unverifiable "
            "(missing key, or fingerprint not in author/platform trusted sets). "
            "Good-but-unregistered is unverifiable — with fail_on that is exit 2, "
            "worse than unsigned."
        )

    if fail_unverifiable and (unverifiable > 0 or other_bad > 0):
        print(
            "ERROR: unverifiable or bad commit signatures present "
            f"(unverifiable={unverifiable}, bad={other_bad})",
            file=sys.stderr,
        )
        return 2

    if enforce and ratio < min_ratio:
        print(
            f"ERROR: signed ratio {ratio:.2f} below required {min_ratio:.2f} "
            f"(author fingerprints only, window last {depth})",
            file=sys.stderr,
        )
        return 1

    if enforce and bool(policy.get("require_head_signed_on_release_tags")) and _on_release_tag():
        if not _head_trusted(author_trusted):
            print(
                "ERROR: release tag HEAD must be signed by an author trusted_signing_keys fingerprint",
                file=sys.stderr,
            )
            return 1

    n59 = bool(policy.get("require_author_signature_on_trusted_keys_dir", False))
    if n59:
        keys_rel = str(policy.get("trusted_keys_dir") or "governance/trusted_signing_keys")
        cutoff = str(policy.get("n59_enforced_after") or "").strip()
        if not cutoff:
            print(
                "ERROR: N-59 enabled but n59_enforced_after is empty "
                "(set to the filter-repo cliff SHA, then keep it)",
                file=sys.stderr,
            )
            return 1
        n59_hits = _n59_unsigned_key_dir_commits(
            rows, author_trusted, keys_rel=keys_rel, cutoff=cutoff
        )
        if n59_hits:
            print(
                "ERROR: N-59: these commits change "
                f"{keys_rel} without an author-trusted signature: "
                + ", ".join(n59_hits),
                file=sys.stderr,
            )
            return 1
        print(f"n59_key_dir_ok=true enforced_after={cutoff}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
