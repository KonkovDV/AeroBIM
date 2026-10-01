"""Advisory drawing-read grounding harness (DrawingVQA-inspired, fixture-only).

WHAT THIS MEASURES: the fidelity of AeroBIM's **deterministic** advisory pipeline
(schema guard -> grounding -> our normalizer -> HITL abstention -> injection
observability) on **replayed / canned** VLM region reads with known expected
outcomes. It is a regression + contract signal for the advisory grounding code.

WHAT THIS IS NOT: it is NOT model accuracy, NOT product accuracy, and NOT customer
drawing-reading evidence. The VLM responses are synthetic fixtures; no model runs.
Real drawing-reading accuracy needs an adjudicated customer corpus (RT-001) and is
never claimed from this harness. Inspired by DrawingVQA (arXiv 2607.15418) only in
spirit (structured reads over drawings), not as a comparable benchmark.

The advisory contour never sets ``summary.passed`` (ADR-001); this harness cannot
change a verdict.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.vlm_grounding import ground_vlm_region_observations
from aerobim.domain.vlm_response_schema import validate_observations_response

_SCHEMA_VERSION = "1.0.0"
_MAX_INPUT_BYTES = 10 * 1024 * 1024
_MAX_CASES = 10_000
_COMPARABLE_KEYS = frozenset(
    {
        "schema_conformant",
        "parse_ok",
        "readable",
        "normalized_values",
        "hitl_count",
        "dropped_count",
        "control_fields_ignored",
    }
)
_SET_KEYS = frozenset({"normalized_values", "control_fields_ignored"})


def _load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"Symlinked cases input is not accepted: {path}")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError(f"Cases path is not a regular file: {path}")
    if path.stat().st_size > _MAX_INPUT_BYTES:
        raise ValueError(f"Cases input exceeds {_MAX_INPUT_BYTES} bytes: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid UTF-8 JSON cases input: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Cases root must be a JSON object")
    if payload.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(f"Cases schema_version must be {_SCHEMA_VERSION!r}")
    return payload


def _actual_outcome(case: dict[str, Any]) -> dict[str, Any]:
    vlm_response = case.get("vlm_response")
    conformant = validate_observations_response(vlm_response).conformant
    result = ground_vlm_region_observations(
        vlm_response,
        sheet_id=str(case.get("sheet_id", "S")),
        region_id=str(case.get("region_id", "r")),
        confidence_calibrated=bool(case.get("confidence_calibrated", False)),
    )
    return {
        "schema_conformant": conformant,
        "parse_ok": result.parse_ok,
        "readable": result.readable,
        "normalized_values": sorted(
            o.normalized_value for o in result.observations if o.normalized_value is not None
        ),
        "hitl_count": result.hitl_count,
        "dropped_count": result.dropped_count,
        "control_fields_ignored": list(result.control_fields_ignored),
    }


def _case_mismatches(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    mismatches: list[str] = []
    for key, want in expected.items():
        if key not in _COMPARABLE_KEYS:
            raise ValueError(f"Unsupported expected key {key!r}")
        got = actual[key]  # always populated by _actual_outcome for comparable keys
        if key in _SET_KEYS:
            if sorted(want) != sorted(got):
                mismatches.append(f"{key}: expected {sorted(want)}, got {sorted(got)}")
        elif want != got:
            mismatches.append(f"{key}: expected {want!r}, got {got!r}")
    return mismatches


def evaluate_drawing_advisory_grounding(cases_path: Path) -> dict[str, object]:
    """Run the deterministic advisory pipeline on canned reads; return a report."""
    payload = _load_json(cases_path)
    dataset_id = str(payload.get("dataset_id") or "unknown")
    dataset_status = str(payload.get("dataset_status") or "synthetic").lower()
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("cases must be a non-empty array")
    if len(raw_cases) > _MAX_CASES:
        raise ValueError(f"cases exceed maximum of {_MAX_CASES}")

    per_case: list[dict[str, Any]] = []
    matched = 0
    seen_ids: set[str] = set()
    for index, case in enumerate(raw_cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be an object")
        case_id = str(case.get("case_id") or f"case-{index}")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate case_id: {case_id}")
        seen_ids.add(case_id)
        expected = case.get("expected")
        if not isinstance(expected, dict) or not expected:
            raise ValueError(f"case {case_id!r} needs a non-empty 'expected' object")
        actual = _actual_outcome(case)
        mismatches = _case_mismatches(expected, actual)
        if not mismatches:
            matched += 1
        per_case.append({"case_id": case_id, "matched": not mismatches, "mismatches": mismatches})

    total = len(per_case)
    fidelity = round(matched / total, 6) if total else 0.0
    warning = None
    if dataset_status != "adjudicated":
        warning = (
            "Advisory grounding fixture: measures the DETERMINISTIC grounding of canned "
            "VLM reads, NOT model or product accuracy, and NOT customer drawing evidence "
            "(RT-001). Not publishable as AeroBIM accuracy."
        )
    return {
        "artifact_type": "aerobim_drawing_advisory_grounding_evaluation",
        "schema_version": _SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "dataset_status": dataset_status,
        "measures": "deterministic advisory grounding pipeline fidelity on replayed reads",
        "does_not_measure": [
            "VLM model accuracy",
            "AeroBIM product accuracy",
            "customer drawing-reading (RT-001)",
        ],
        "total_cases": total,
        "matched_cases": matched,
        "grounding_fidelity": fidelity,
        "per_case": per_case,
        "warning": warning,
    }


def threshold_failures(
    report: dict[str, object], *, min_fidelity: float | None = None
) -> list[str]:
    failures: list[str] = []
    if min_fidelity is None:
        return failures
    if not 0.0 <= min_fidelity <= 1.0:
        raise ValueError("min_fidelity threshold must be in [0, 1]")
    actual = float(report["grounding_fidelity"])  # type: ignore[arg-type]
    if actual < min_fidelity:
        failures.append(f"grounding_fidelity {actual:.6f} < required {min_fidelity:.6f}")
    return failures


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic advisory drawing-read grounding fidelity (fixture-only)"
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--min-fidelity", type=float)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_drawing_advisory_grounding(args.cases)
    failures = threshold_failures(report, min_fidelity=args.min_fidelity)
    report["gate"] = {
        "passed": not failures,
        "failures": failures,
        "thresholds": {"min_fidelity": args.min_fidelity},
    }
    if args.output is not None:
        _write_json_atomic(args.output, report)
    print(
        json.dumps(
            {
                "dataset_id": report["dataset_id"],
                "grounding_fidelity": report["grounding_fidelity"],
                "matched_cases": report["matched_cases"],
                "total_cases": report["total_cases"],
                "gate_passed": not failures,
                "warning": report["warning"],
            },
            ensure_ascii=False,
        )
    )
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
