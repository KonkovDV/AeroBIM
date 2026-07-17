"""CI harness for advisory IFC QA (RU fixture) — not IfcLLM product accuracy.

Evaluates RelationalIfcKnowledgeGraph against a frozen question set.
Scores are fixture-only; never publish as AeroBIM product precision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aerobim.infrastructure.adapters.relational_ifc_knowledge_graph import (
    RelationalIfcKnowledgeGraph,
)


def evaluate_ifc_qa(
    questions_path: Path,
    ifc_path: Path,
) -> dict[str, object]:
    payload = json.loads(questions_path.read_text(encoding="utf-8"))
    if payload.get("dataset_status") == "adjudicated":
        raise ValueError("adjudicated IFC-QA customer sets are not yet wired; use synthetic/draft")
    kg = RelationalIfcKnowledgeGraph()
    results: list[dict[str, object]] = []
    passed = 0
    for case in payload.get("cases", []):
        question = str(case["question"])
        min_guids = int(case.get("min_guids", 0))
        outcome = kg.query_nl(question, ifc_path=ifc_path)
        ok = (not outcome.degraded) and len(outcome.element_guids) >= min_guids
        if min_guids == 0 and outcome.backend == "relational":
            ok = True
        if ok:
            passed += 1
        results.append(
            {
                "question_id": case.get("question_id"),
                "ok": ok,
                "guid_count": len(outcome.element_guids),
                "backend": outcome.backend,
                "degraded": outcome.degraded,
                "reason": outcome.reason,
            }
        )
    total = len(results) or 1
    return {
        "artifact_type": "aerobim_ifc_qa_fixture_evaluation",
        "schema_version": "1.0.0",
        "dataset_id": payload.get("dataset_id"),
        "claim_boundary": payload.get("claim_boundary"),
        "ifc_path": str(ifc_path.as_posix()),
        "passed": passed,
        "total": len(results),
        "accuracy": round(passed / total, 6),
        "warning": (
            "Fixture accuracy only — never publish as product; "
            "IfcLLM 93–100% on 30 scenarios is external literature, not AeroBIM"
        ),
        "cases": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--ifc", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--min-accuracy", type=float, default=None)
    args = parser.parse_args(argv)
    report = evaluate_ifc_qa(args.questions, args.ifc)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.min_accuracy is not None:
        accuracy = report["accuracy"]
        if not isinstance(accuracy, (int, float)):
            raise TypeError(f"accuracy must be numeric, got {type(accuracy)!r}")
        if float(accuracy) < args.min_accuracy:
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
