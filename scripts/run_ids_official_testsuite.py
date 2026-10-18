#!/usr/bin/env python3
"""Run the official buildingSMART IDS 1.0 TestCases (290 pinned pairs) in CI.

Two numbers per run, both against the same pinned, unmodified cases
(samples/ids/buildingsmart-testcases, CC BY-ND 4.0):

* ``aerobim``: the product path (VALIDATE_IFC_AGAINST_IDS use case), including
  AeroBIM's intentional fail-closed gates. Mismatches are split into labelled
  upstream IfcTester edges, labelled AeroBIM fail-closed divergences and
  unexplained ones. Exit code 2 if any mismatch is unexplained.
* ``ifctester``: the bare engine (IfcTester on the IfcOpenShell kernel) for
  reference, with no AeroBIM gates. Informational only.

Regression fidelity on conformance fixtures, not product accuracy.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROFILE = (
    REPO
    / "samples"
    / "benchmarks"
    / "open-corpora"
    / "profiles"
    / "regression-bsi.json"
)


def _engine_only(profile: dict[str, object]) -> dict[str, object]:
    import ifcopenshell
    import ifctester
    from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model
    from aerobim.infrastructure.adapters.xml_ids_document_auditor import (
        ensure_ifctester_offline_schema,
    )
    from ifctester import ids

    ensure_ifctester_offline_schema()

    rows: list[dict[str, object]] = []
    for case in profile["cases"]:  # type: ignore[union-attr]
        expected = bool(case["expected_passed"])
        try:
            spec = ids.open(str(REPO / case["ids_path"]))
            spec.validate(open_ifc_model(REPO / case["ifc_path"]))
            actual: bool | None = all(bool(s.status) for s in spec.specifications)
            error = None
        except Exception as exc:  # noqa: BLE001 - an engine crash counts as a mismatch
            actual, error = None, f"{type(exc).__name__}: {str(exc)[:160]}"
        rows.append(
            {
                "case_id": case["case_id"],
                "expected_passed": expected,
                "actual_passed": actual,
                "match": actual == expected,
                "error": error,
            }
        )
    matched = sum(1 for row in rows if row["match"])
    return {
        "ifcopenshell": str(ifcopenshell.version),
        "ifctester": str(getattr(ifctester, "__version__", "unknown")),
        "cases_run": len(rows),
        "cases_matched": matched,
        "mismatch_case_ids": [row["case_id"] for row in rows if not row["match"]],
        "errors": [row for row in rows if row["error"]],
    }


def _markdown(result: dict[str, object]) -> str:
    a = result["aerobim"]
    e = result["ifctester"]
    assert isinstance(a, dict) and isinstance(e, dict)
    by_kind: dict[str, list[int]] = {"pass": [0, 0], "fail": [0, 0]}
    for row in a["cases"]:
        kind = "pass" if row["expected_passed"] else "fail"
        by_kind[kind][0] += 1
        by_kind[kind][1] += int(bool(row["match"]))
    lines = [
        "### buildingSMART IDS 1.0 TestCases",
        "",
        f"Upstream commit `{result['upstream_commit']}`; kernel ifcopenshell "
        f"{e['ifcopenshell']}, ifctester {e['ifctester']}; {result['elapsed_s']} s.",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| cases | {a['cases_run']} |",
        f"| AeroBIM matched (raw) | {a['cases_matched']} ({a['binary_match_rate']:.1%}) |",
        f"| expected-pass cases matched | {by_kind['pass'][1]} / {by_kind['pass'][0]} |",
        f"| expected-fail cases matched | {by_kind['fail'][1]} / {by_kind['fail'][0]} |",
        f"| mismatches: labelled upstream IfcTester edges | {a['known_upstream_mismatch_count']} |",
        f"| mismatches: labelled AeroBIM fail-closed divergences | {a['fail_closed_divergence_count']} |",
        f"| mismatches: unexplained | {a['unexplained_mismatch_count']} |",
        f"| scorable (unlabelled) matched | {a['adjusted_cases_matched']} / {a['adjusted_cases_scorable']} |",
        f"| bare IfcTester engine matched | {e['cases_matched']} / {e['cases_run']} |",
        "",
    ]
    if a["unexplained_case_ids"]:
        lines += ["Unexplained mismatches:", ""]
        lines += [f"- `{case}`" for case in a["unexplained_case_ids"]]
        lines.append("")
    lines += ["Bare-engine mismatches:", ""]
    lines += [f"- `{case}`" for case in e["mismatch_case_ids"]] or ["- none"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    from aerobim.tools.run_open_corpora_profiles import run_regression_profile

    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as storage:
        aerobim = run_regression_profile(profile, repo=REPO, storage_dir=Path(storage))
    engine = _engine_only(profile)
    result = {
        "upstream_commit": profile["source"]["upstream_commit"],
        "elapsed_s": round(time.perf_counter() - started, 1),
        "aerobim": aerobim,
        "ifctester": engine,
    }
    args.out_json.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    args.out_md.write_text(_markdown(result), encoding="utf-8")
    print(_markdown(result))
    return 0 if aerobim.get("regression_pass") else 2


if __name__ == "__main__":
    sys.exit(main())
