"""Evaluate advisory LLM extraction vs regex baseline (fixture_only).

Never mutates summary.passed. Offline/mock when LLM keys are absent.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.llm_extraction import ExtractionCandidate, LlmExtractionPort
from aerobim.infrastructure.di.bootstrap import bootstrap_container

CLAIM_LEVEL = "fixture_only"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return "".join(ch for ch in value.lower().strip() if ch.isalnum() or ch in {".", ",", "-", "/"})


def _candidate_key(candidate: ExtractionCandidate | dict[str, Any]) -> tuple[str, str, str, str]:
    if isinstance(candidate, ExtractionCandidate):
        return (
            _normalize(candidate.ifc_entity),
            _normalize(candidate.property_set),
            _normalize(candidate.property_name),
            _normalize(candidate.expected_value),
        )
    return (
        _normalize(str(candidate.get("ifc_entity") or "")),
        _normalize(str(candidate.get("property_set") or "")),
        _normalize(str(candidate.get("property_name") or "")),
        _normalize(str(candidate.get("expected_value") or "")),
    )


def _gt_key(rule: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _normalize(str(rule.get("ifc_entity") or "")),
        _normalize(str(rule.get("property_set") or "")),
        _normalize(str(rule.get("property_name") or "")),
        _normalize(str(rule.get("expected_value") or "")),
    )


def score_against_ground_truth(
    candidates: Sequence[ExtractionCandidate],
    ground_truth: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    scored = [c for c in candidates if c.status == "ok"]
    gt_keys = {_gt_key(rule) for rule in ground_truth}
    pred_keys = {_candidate_key(c) for c in scored}
    tp = len(gt_keys & pred_keys)
    fp = len(pred_keys - gt_keys)
    fn = len(gt_keys - pred_keys)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    hallucinations = sum(1 for c in scored if not c.evidence_refs)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "macro_f1": round(f1, 4),
        "hallucination_count": hallucinations,
        "candidate_count": len(scored),
        "gt_count": len(ground_truth),
    }


def _load_corpus(path: Path, repo: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    fixtures = payload.get("fixtures") if isinstance(payload, dict) else None
    if not isinstance(fixtures, list):
        raise ValueError("corpus must contain fixtures[]")
    rows: list[dict[str, Any]] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        source_rel = str(fixture.get("source_path") or "")
        source_path = (repo / source_rel).resolve()
        if not source_path.exists():
            continue
        gt = fixture.get("ground_truth_requirements")
        if not isinstance(gt, list):
            continue
        rows.append(
            {
                "fixture_id": str(fixture.get("fixture_id") or source_path.name),
                "source_path": source_rel,
                "text": source_path.read_text(encoding="utf-8"),
                "ground_truth": [item for item in gt if isinstance(item, dict)],
            }
        )
    return rows


def _run_provider(name: str, port: LlmExtractionPort, text: str, source_id: str) -> dict[str, Any]:
    started = perf_counter()
    candidates = port.extract_candidates(text, source_id=source_id)
    elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
    statuses = {c.status for c in candidates}
    live = "ok" in statuses and name != "regex"
    return {
        "provider": name,
        "elapsed_ms": elapsed_ms,
        "live_provider": live if name != "regex" else False,
        "statuses": sorted(statuses),
        "candidates": [asdict(c) for c in candidates],
        "raw_candidates": candidates,
    }


def evaluate_llm_extraction(
    corpus_path: Path | None = None,
    *,
    write_evidence: bool = False,
) -> dict[str, Any]:
    repo = _repo_root()
    corpus = corpus_path or (repo / "samples" / "benchmarks" / "russian-aec-ground-truth.json")
    fixtures = _load_corpus(corpus, repo)
    if not fixtures:
        raise FileNotFoundError(f"No usable fixtures in {corpus}")

    container = bootstrap_container(Settings.from_env())
    providers: dict[str, LlmExtractionPort] = {
        "regex": container.resolve(Tokens.LLM_EXTRACTION_REGEX),
        "kimi": container.resolve(Tokens.LLM_EXTRACTION_KIMI),
        "qwen": container.resolve(Tokens.LLM_EXTRACTION_QWEN),
    }

    per_fixture: list[dict[str, Any]] = []
    aggregate: dict[str, list[dict[str, Any]]] = {name: [] for name in providers}
    any_live = False

    for fixture in fixtures:
        fixture_row: dict[str, Any] = {
            "fixture_id": fixture["fixture_id"],
            "source_path": fixture["source_path"],
            "providers": {},
        }
        for name, port in providers.items():
            run = _run_provider(name, port, fixture["text"], fixture["fixture_id"])
            metrics = score_against_ground_truth(run["raw_candidates"], fixture["ground_truth"])
            if run["live_provider"]:
                any_live = True
            provider_payload = {
                "elapsed_ms": run["elapsed_ms"],
                "live_provider": run["live_provider"],
                "statuses": run["statuses"],
                "metrics": metrics,
                "candidate_count": len(run["candidates"]),
            }
            fixture_row["providers"][name] = provider_payload
            aggregate[name].append(metrics)
        per_fixture.append(fixture_row)

    def _macro_mean(rows: list[dict[str, Any]]) -> dict[str, float]:
        if not rows:
            return {"precision": 0.0, "recall": 0.0, "macro_f1": 0.0, "hallucination_count": 0.0}
        return {
            "precision": round(sum(r["precision"] for r in rows) / len(rows), 4),
            "recall": round(sum(r["recall"] for r in rows) / len(rows), 4),
            "macro_f1": round(sum(r["macro_f1"] for r in rows) / len(rows), 4),
            "hallucination_count": round(
                sum(r["hallucination_count"] for r in rows) / len(rows), 4
            ),
        }

    summary = {name: _macro_mean(rows) for name, rows in aggregate.items()}
    if any_live:
        conclusion = (
            "On this fixture corpus, compare macro_f1 in summary; "
            "LLM value vs regex is established only for live providers that ran."
        )
    else:
        conclusion = (
            "Live Kimi/Qwen extraction did not run (no API keys / provider not ready); "
            "only regex baseline scored on fixtures — LLM worth-it vs regex is not established."
        )

    payload: dict[str, Any] = {
        "artifact_type": "llm_extraction_kimi_vs_qwen",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": CLAIM_LEVEL,
        "customer_accuracy_not_established": True,
        "live_provider": any_live,
        "corpus_path": str(corpus.resolve()),
        "fixture_count": len(fixtures),
        "summary": summary,
        "fixtures": per_fixture,
        "conclusion": conclusion,
    }

    if write_evidence:
        json_path = repo / "docs" / "evidence" / "llm-extraction-kimi-vs-qwen-2026-08.json"
        md_path = repo / "docs" / "evidence" / "llm-extraction-kimi-vs-qwen-2026-08.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = json_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(json_path)
        lines = [
            "# LLM extraction — Kimi vs Qwen (2026-08)",
            "",
            "**claim_level:** `fixture_only` · **live_provider:** "
            f"`{str(any_live).lower()}` · Experimental advisory only (not verdict).",
            "",
            "| Provider | macro_f1 | precision | recall | halluc/fixture |",
            "|---|---:|---:|---:|---:|",
        ]
        for name in ("regex", "kimi", "qwen"):
            row = summary.get(name, {})
            lines.append(
                f"| {name} | {row.get('macro_f1')} | {row.get('precision')} | "
                f"{row.get('recall')} | {row.get('hallucination_count')} |"
            )
        lines.extend(["", f"**Conclusion:** {conclusion}", ""])
        md_path.write_text("\n".join(lines), encoding="utf-8")
        payload["evidence_json"] = str(json_path)
        payload["evidence_md"] = str(md_path)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate advisory LLM extraction (fixture_only)")
    parser.add_argument("--corpus", type=Path, default=None)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = evaluate_llm_extraction(args.corpus, write_evidence=args.write_evidence)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
