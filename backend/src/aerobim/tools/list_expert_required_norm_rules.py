"""List norm-pack rules that cannot be auto-checked (execution_mode=expert_required).

Usage:
  python -m aerobim.tools.list_expert_required_norm_rules --pack PATH
  python -m aerobim.tools.list_expert_required_norm_rules --pack PATH --output report.json

Honesty: listing only. Does not grant customer_approved status or close RT-002.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.domain.norm_rule_eligibility import expert_required_report
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "List expert_required / awaiting-confirmation norm rules "
            "(WP-04; does not close RT-002)."
        )
    )
    parser.add_argument(
        "--pack",
        type=Path,
        required=True,
        help="Path to a norm rule pack JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path (stdout when omitted)",
    )
    args = parser.parse_args(argv)

    pack = JsonNormRulePackLoader().load(args.pack)
    report = expert_required_report(pack)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
