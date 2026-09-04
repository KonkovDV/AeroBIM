"""KT#2 one-command vertical slice. Fail-loud. fixture_only. No new ports.

Needed for demo 20.08: one CLI a clean machine can run from README.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.run_vertical_slice import _REPO, run_vertical_slice

_DEFAULT_MANIFEST = _REPO / "samples" / "demo" / "vertical-slice-2026-08-11" / "manifest.json"
_DEFAULT_OUTPUT = _REPO / "artifacts" / "vertical-slice-demo"


class DemoSliceError(RuntimeError):
    """Operator-visible failure: missing input or incomplete artifacts."""


def _require_file(path: Path, what: str) -> None:
    if not path.is_file():
        raise DemoSliceError(f"{what} missing: {path}")


def run_demo_vertical_slice(
    *,
    manifest: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    pack = (manifest or _DEFAULT_MANIFEST).expanduser().resolve()
    out = (output_dir or _DEFAULT_OUTPUT).expanduser().resolve()
    _require_file(pack, "manifest")
    pdf = (
        _REPO / "samples" / "demo" / "vertical-slice-2026-08-11" / "techlab-a101-wall-thickness.pdf"
    )
    _require_file(pdf, "demo PDF")

    summary = run_vertical_slice(pack, out)
    if int(summary.get("drawing_annotation_count") or 0) < 1:
        raise DemoSliceError(
            "zero drawing annotations — not a silent pass; check PDF text layer / analyzer"
        )
    raw_paths = summary.get("_paths")
    paths: dict[str, Any] = raw_paths if isinstance(raw_paths, dict) else {}
    _require_file(Path(str(paths.get("report_json") or out / "report.json")), "report.json")
    _require_file(Path(str(paths.get("report_html") or out / "report.html")), "report.html")
    _require_file(Path(str(paths.get("bcf_zip") or out / "findings.bcfzip")), "BCF ZIP")
    _require_file(
        Path(str(paths.get("run_manifest") or out / "run-manifest.json")),
        "run-manifest.json",
    )
    _require_file(
        Path(str(paths.get("summary") or out / "slice-summary.json")),
        "slice-summary.json",
    )
    overlay = out / "overlay-problem-zone.png"
    if summary.get("overlay_error"):
        raise DemoSliceError(f"overlay failed: {summary['overlay_error']}")
    _require_file(overlay, "overlay PNG")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        result = run_demo_vertical_slice(manifest=args.manifest, output_dir=args.output)
    except (DemoSliceError, FileNotFoundError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    public = {k: v for k, v in result.items() if k != "_paths"}
    print(json.dumps(public, ensure_ascii=False, indent=2, default=str))
    passed = bool((result.get("summary") or {}).get("passed"))
    outcome = result.get("outcome")
    print(
        "VERDICT: NOT PASS — fixture demo, not customer accuracy. "
        f"summary.passed={str(passed).lower()} outcome={outcome} "
        f"checkpoint={CHECKPOINT} customer_go=false expert_review_required=true",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
