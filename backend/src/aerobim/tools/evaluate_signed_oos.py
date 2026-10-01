"""Evaluate a signed OOS JSON. Unsigned templates do not license skip."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aerobim.domain.signed_oos import evaluate_oos, oos_snapshot, unsigned_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument(
        "--print-template",
        choices=("qto_space_area", "mep_federated", "rebar_class4"),
        default=None,
    )
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args(argv)

    if args.snapshot:
        print(json.dumps(oos_snapshot(), ensure_ascii=False, indent=2))
        return 0
    if args.print_template:
        print(json.dumps(unsigned_template(args.print_template), ensure_ascii=False, indent=2))
        return 0
    if args.input is None:
        parser.error("provide --input, --print-template, or --snapshot")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    decision = evaluate_oos(payload)
    print(json.dumps(decision.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
