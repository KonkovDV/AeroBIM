"""Write the TZ accuracy-answer artifact from committed evidence files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.domain.accuracy_answer import assemble_accuracy_answer, render_accuracy_answer_markdown


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export accuracy-answer artifact (not product %)")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="defaults to docs/evidence/accuracy-answer-2026-09.json",
    )
    args = parser.parse_args(argv)
    root = args.repo or repo_root()
    payload = assemble_accuracy_answer(root)
    out_json = args.out_json or (root / "docs" / "evidence" / "accuracy-answer-2026-09.json")
    out_md = out_json.with_suffix(".md")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_accuracy_answer_markdown(payload), encoding="utf-8")
    print(out_json)
    print(out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
