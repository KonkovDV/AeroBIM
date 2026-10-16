#!/usr/bin/env python3
"""Render a markdown comparison of two ifc_kernel_compare.py results."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    old = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    new = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    ko = old["fixtures"]["_kernel"]["ifcopenshell"]
    kn = new["fixtures"]["_kernel"]["ifcopenshell"]
    lines = [
        f"### Package `{old['package']['pack']}`",
        "",
        f"| metric | {ko} | {kn} |",
        "|---|---|---|",
    ]
    for key in (
        "issue_count",
        "requirement_count",
        "analyze_ms",
        "process_wall_s",
        "peak_rss_kib",
    ):
        lines.append(f"| {key} | {old['package'][key]} | {new['package'][key]} |")
    lines += [
        "",
        "### Fixtures that differ (entities / schema / error)",
        "",
        f"| file | {ko} | {kn} |",
        "|---|---|---|",
    ]
    same = 0
    for rel in sorted(set(old["fixtures"]) | set(new["fixtures"])):
        if rel == "_kernel":
            continue
        a, b = old["fixtures"].get(rel, {}), new["fixtures"].get(rel, {})
        fa = (a.get("entities"), a.get("schema"), a.get("error"))
        fb = (b.get("entities"), b.get("schema"), b.get("error"))
        if fa == fb:
            same += 1
            continue
        lines.append(f"| {rel} | {fa} | {fb} |")
    total_a = sum(v.get("ms", 0) for k, v in old["fixtures"].items() if k != "_kernel")
    total_b = sum(v.get("ms", 0) for k, v in new["fixtures"].items() if k != "_kernel")
    lines += [
        "",
        f"Identical entity count + schema: {same} fixtures. Sum of open times: {total_a:.1f} ms vs {total_b:.1f} ms.",
    ]
    for name in sorted(set(old.get("external", {})) | set(new.get("external", {}))):
        a = old.get("external", {}).get(name, {})
        b = new.get("external", {}).get(name, {})
        lines += [
            "",
            f"### Large real model `{name}`",
            "",
            f"| metric | {ko} | {kn} |",
            "|---|---|---|",
        ]
        for key in (
            "schema",
            "entities",
            "products",
            "walls",
            "open_s",
            "peak_rss_kib",
        ):
            lines.append(
                f"| open.{key} | {a.get('open', {}).get(key)} | {b.get('open', {}).get(key)} |"
            )
        for key in (
            "issue_count",
            "requirement_count",
            "analyze_ms",
            "process_wall_s",
            "peak_rss_kib",
        ):
            lines.append(
                f"| package.{key} | {a.get('package', {}).get(key)} | {b.get('package', {}).get(key)} |"
            )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
