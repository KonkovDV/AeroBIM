"""Write a git-safe customer delivery index into .local/. Never docs/ or samples/."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.domain.customer_delivery_index import (
    empty_delivery_index,
    validate_delivery_index,
)
from aerobim.domain.customer_review_book import assert_output_path_allowed


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def assert_index_path_allowed(path: Path, *, repo: Path) -> None:
    assert_output_path_allowed(path.parent if path.suffix else path, repo=repo)
    resolved = path.resolve()
    rel = ""
    try:
        rel = resolved.relative_to(repo.resolve()).as_posix()
    except ValueError:
        return
    for prefix in ("docs/", "samples/", "submission/", "frontend/"):
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            raise ValueError(f"refuses to write delivery index under {prefix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export three-pack + trial delivery index (not customer reports)"
    )
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--from-json", type=Path, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="defaults to <repo>/.local/pack-out/delivery-index.json",
    )
    args = parser.parse_args(argv)
    root = (args.repo or repo_root()).resolve()
    if args.from_json is None:
        payload = empty_delivery_index()
    else:
        raw = json.loads(args.from_json.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise SystemExit("from-json must be an object")
        payload = validate_delivery_index(raw)
    out = args.output or (root / ".local" / "pack-out" / "delivery-index.json")
    assert_index_path_allowed(out, repo=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out)
    print(f"ready_for_deadline={payload['ready_for_deadline']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
