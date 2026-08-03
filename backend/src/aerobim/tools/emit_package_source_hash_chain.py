"""CLI: emit / compare package source hash chains (RT-021 eng, read-only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.domain.package_source_integrity import (
    build_package_source_hash_chain,
    compare_hash_chains,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package source SHA-256 hash chain (read-only; not УКЭП)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit", help="Build hash chain for listed paths under --root")
    emit.add_argument("--root", type=Path, required=True)
    emit.add_argument("--path", type=Path, action="append", default=[])
    emit.add_argument("--package-id", default=None)
    emit.add_argument("--output", type=Path, default=None)

    diff = sub.add_parser("diff", help="Compare intake vs current chain JSON")
    diff.add_argument("--expected", type=Path, required=True)
    diff.add_argument("--observed", type=Path, required=True)
    diff.add_argument("--output", type=Path, default=None)

    args = parser.parse_args()
    if args.command == "emit":
        if not args.path:
            print("--path required at least once", file=sys.stderr)
            raise SystemExit(2)
        payload = build_package_source_hash_chain(
            root=args.root,
            paths=args.path,
            package_id=args.package_id,
        )
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        raise SystemExit(0 if payload.get("status") == "ok" else 2)

    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    observed = json.loads(args.observed.read_text(encoding="utf-8"))
    payload = compare_hash_chains(expected, observed)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    raise SystemExit(0 if payload.get("match") else 2)


if __name__ == "__main__":
    main()
