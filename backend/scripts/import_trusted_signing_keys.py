#!/usr/bin/env python3
"""Import ASCII-armored public keys from governance/trusted_signing_keys into GnuPG.

CI runners start with an empty keyring. Without this step, signed commits stay
``E`` (unverifiable) and ``fail_on_unverifiable_signature`` fails for the wrong
reason. Keys in this directory are public material; the script also marks them
ultimately trusted in the *ephemeral* CI keyring so git ``%G?`` returns ``G``.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
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


def _run(gpg: str, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [gpg, *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _fingerprints_after_import(gpg: str, before: set[str]) -> list[str]:
    proc = _run(gpg, ["--with-colons", "--list-keys"])
    found: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.startswith("fpr:"):
            continue
        parts = line.split(":")
        if len(parts) > 9 and parts[9]:
            fpr = parts[9].upper()
            if fpr not in before:
                found.append(fpr)
    return found


def _list_fingerprints(gpg: str) -> set[str]:
    proc = _run(gpg, ["--with-colons", "--list-keys"])
    out: set[str] = set()
    for line in proc.stdout.splitlines():
        if line.startswith("fpr:"):
            parts = line.split(":")
            if len(parts) > 9 and parts[9]:
                out.add(parts[9].upper())
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keys-dir",
        type=Path,
        default=_repo_root() / "governance/trusted_signing_keys",
    )
    parser.add_argument(
        "--require-at-least",
        type=int,
        default=1,
        help="Fail if fewer than N .asc files are imported",
    )
    args = parser.parse_args()
    gpg = _gpg_bin()
    if not args.keys_dir.is_dir():
        print(f"ERROR: keys dir missing: {args.keys_dir}", file=sys.stderr)
        return 1
    asc_files = sorted(args.keys_dir.glob("*.asc"))
    platform_dir = args.keys_dir / "platform"
    if platform_dir.is_dir():
        asc_files.extend(sorted(platform_dir.glob("*.asc")))
    if len(asc_files) < args.require_at_least:
        print(
            f"ERROR: need >= {args.require_at_least} .asc under {args.keys_dir} "
            f"(author + platform/), found {len(asc_files)}",
            file=sys.stderr,
        )
        return 1

    before = _list_fingerprints(gpg)
    imported = 0
    for path in asc_files:
        proc = _run(gpg, ["--import", str(path)])
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            print(f"ERROR: gpg --import failed for {path.name}", file=sys.stderr)
            return 1
        imported += 1
        print(f"imported {path.name}")

    after = _list_fingerprints(gpg)
    new_fprs = sorted(after - before) or sorted(after)
    # Ultimate trust (ownertrust 6) so git %G? reports G not U for these keys.
    trust_blob = "".join(f"{fpr}:6:\n" for fpr in new_fprs if re.fullmatch(r"[0-9A-F]{40}", fpr))
    if trust_blob:
        proc = _run(gpg, ["--import-ownertrust"], input_text=trust_blob)
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            print("ERROR: gpg --import-ownertrust failed", file=sys.stderr)
            return 1
        print(f"ownertrust_ultimate count={len(trust_blob.strip().splitlines())}")

    print(f"trusted_signing_keys imported={imported} fingerprints={len(after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
