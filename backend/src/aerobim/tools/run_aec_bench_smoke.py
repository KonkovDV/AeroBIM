"""AEC-Bench inventory + asset prefetch smoke (Harbor agent trial optional).

``claim_level=open_bench_only``. Prefetch does not need LLM keys; Harbor agent
trials need valid ``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` and Docker.

Dataset: https://github.com/nomic-ai/aec-bench (Apache 2.0).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any

CLAIM_BOUNDARY = (
    "AEC-Bench open_bench_only (arXiv:2603.29199). Prefetch/inventory of public "
    "agentic tasks plus gold-label inventory. Harbor agent trial scores are NOT "
    "AeroBIM product accuracy and do not close RT-001. "
    "null_always_clean is a gold-only baseline, not a drawing-reading agent."
)

_VIOLATION_DETERMINATIONS = frozenset({"rejected", "revise_and_resubmit"})
_CLEAN_DETERMINATIONS = frozenset({"approved", "approved_as_noted"})


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_dataset_root() -> Path:
    env = (os.getenv("AEROBIM_AEC_BENCH_ROOT") or "").strip()
    if env:
        return Path(env)
    return repo_root() / ".local" / "aec-bench"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _secret_present(name: str) -> bool:
    """True if the named secret is in the process env or backend/.env. Never returns the value."""
    if (os.getenv(name) or "").strip():
        return True
    env_path = repo_root() / "backend" / ".env"
    if not env_path.is_file():
        return False
    prefix = f"{name}="
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped.startswith(prefix):
            continue
        value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
        return bool(value)
    return False


def discover_instances(dataset_root: Path) -> list[dict[str, Any]]:
    tasks_root = dataset_root / "tasks"
    instances: list[dict[str, Any]] = []
    if not tasks_root.is_dir():
        return instances
    for scope_dir in sorted(p for p in tasks_root.iterdir() if p.is_dir()):
        for family_dir in sorted(p for p in scope_dir.iterdir() if p.is_dir()):
            for inst_dir in sorted(p for p in family_dir.iterdir() if p.is_dir()):
                manifest = inst_dir / "environment" / "manifest.jsonl"
                instances.append(
                    {
                        "scope": scope_dir.name,
                        "family": family_dir.name,
                        "instance": inst_dir.name,
                        "path": str(inst_dir.relative_to(dataset_root)),
                        "has_manifest": manifest.is_file(),
                    }
                )
    return instances


def prefetch_instance(
    dataset_root: Path,
    *,
    scope: str,
    family: str,
    instance: str,
    timeout_s: float,
    retries: int = 3,
) -> dict[str, Any]:
    inst_dir = dataset_root / "tasks" / scope / family / instance
    manifest = inst_dir / "environment" / "manifest.jsonl"
    if not manifest.is_file():
        return {"status": "error", "detail": f"missing manifest {manifest}"}

    env_dir = inst_dir / "environment"
    downloads: list[dict[str, Any]] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        url = str(row.get("key") or "")
        dest_name = str(row.get("dest") or "")
        if not url or not dest_name:
            downloads.append({"status": "error", "detail": "bad manifest row"})
            continue
        dest = env_dir / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and dest.stat().st_size > 0:
            downloads.append(
                {
                    "dest": dest_name,
                    "status": "cached",
                    "bytes": dest.stat().st_size,
                }
            )
            continue
        last_error = ""
        data: bytes | None = None
        for attempt in range(max(1, retries)):
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 AeroBIM-open-bench/1.0"},
                    method="GET",
                )
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    data = resp.read()
                break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                last_error = str(exc)[:300]
                data = None
                if attempt + 1 < retries:
                    sleep(1.5 * (attempt + 1))
        if data is None:
            downloads.append({"dest": dest_name, "status": "error", "detail": last_error})
            continue
        dest.write_bytes(data)
        downloads.append(
            {
                "dest": dest_name,
                "status": "downloaded",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    ok = all(item.get("status") in {"cached", "downloaded"} for item in downloads)
    return {
        "status": "ok" if ok else "partial_or_failed",
        "scope": scope,
        "family": family,
        "instance": instance,
        "downloads": downloads,
    }


def inventory_pdf_assets(dataset_root: Path) -> dict[str, Any]:
    tasks = dataset_root / "tasks"
    pdfs = list(tasks.rglob("*.pdf")) if tasks.is_dir() else []
    by_scope: dict[str, int] = {}
    for path in pdfs:
        try:
            scope = path.relative_to(tasks).parts[0]
        except ValueError:
            scope = "unknown"
        by_scope[scope] = by_scope.get(scope, 0) + 1
    manifest_pdf_urls = 0
    for manifest in tasks.rglob("manifest.jsonl") if tasks.is_dir() else []:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            dest = str(json.loads(line).get("dest") or "")
            if dest.lower().endswith(".pdf"):
                manifest_pdf_urls += 1
    return {
        "pdf_files": len(pdfs),
        "pdf_bytes": sum(path.stat().st_size for path in pdfs),
        "by_scope": by_scope,
        "manifest_pdf_urls": manifest_pdf_urls,
        "note": "Sheets stay gitignored under .local/aec-bench. Not Harbor. Not product accuracy.",
    }


def classify_gold_task(payload: dict[str, Any]) -> str:
    """Map one AEC-Bench gt.json to a compliance label. Not an agent score."""
    determination = str(payload.get("expected_determination") or "").strip().casefold()
    if determination in _VIOLATION_DETERMINATIONS:
        return "has_issue"
    if determination in _CLEAN_DETERMINATIONS:
        return "clean"
    variant = str(payload.get("variant") or "").strip().casefold()
    if variant == "navigation":
        return "qa"
    if variant == "broken":
        return "has_issue"
    if variant == "clean":
        return "clean"
    defects = payload.get("defects")
    if isinstance(defects, list):
        return "has_issue" if defects else "clean"
    if payload.get("expected_answers") is not None:
        return "qa"
    return "unclassified"


def inventory_gold(dataset_root: Path) -> dict[str, Any]:
    tasks_root = dataset_root / "tasks"
    by_label: dict[str, int] = {}
    by_variant: dict[str, int] = {}
    by_family: dict[str, dict[str, int]] = {}
    gt_files = 0
    for gt_path in sorted(tasks_root.rglob("gt.json")) if tasks_root.is_dir() else []:
        gt_files += 1
        payload = json.loads(gt_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            label = "unclassified"
        else:
            label = classify_gold_task(payload)
            variant = str(payload.get("variant") or "none")
            by_variant[variant] = by_variant.get(variant, 0) + 1
        by_label[label] = by_label.get(label, 0) + 1
        try:
            rel = gt_path.relative_to(tasks_root).parts
            family = "/".join(rel[:2]) if len(rel) >= 2 else "unknown"
        except ValueError:
            family = "unknown"
        bucket = by_family.setdefault(family, {})
        bucket[label] = bucket.get(label, 0) + 1
    false_positive = int(by_label.get("has_issue") or 0)
    true_negative = int(by_label.get("clean") or 0)
    labeled = false_positive + true_negative
    return {
        "status": "RUN" if gt_files else "SKIPPED",
        "gt_files": gt_files,
        "by_label": dict(sorted(by_label.items())),
        "by_variant": dict(sorted(by_variant.items())),
        "by_family": {key: dict(sorted(val.items())) for key, val in sorted(by_family.items())},
        "null_always_clean": {
            "claim_boundary": (
                "Always predict compliant without reading drawings. "
                "Not Harbor. Not AeroBIM product accuracy. Not RT-001."
            ),
            "true_positive": 0,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": 0,
            "excluded_qa_or_unclassified": int(by_label.get("qa") or 0)
            + int(by_label.get("unclassified") or 0),
            "labeled_compliance_tasks": labeled,
            "false_pass_rate_on_labeled": (
                round(false_positive / labeled, 4) if labeled else None
            ),
        },
    }


def render_false_pass_markdown(payload: dict[str, Any]) -> str:
    gold = payload.get("gold") or {}
    null = gold.get("null_always_clean") or {}
    harbor = payload.get("agent_trial") or {}
    return "\n".join(
        [
            "<!-- claims-lint: allow-file reason=\"AEC-Bench gold inventory; Harbor false-pass SKIPPED\" -->",
            "---",
            'title: "AEC-Bench gold inventory and null baseline"',
            f"date: {str(payload.get('generated_at') or '')[:10]}",
            f"claim_level: {payload.get('claim_level')}",
            "claim_boundary: >-",
            f"  {payload.get('claim_boundary')}",
            "---",
            "",
            "# AEC-Bench gold inventory",
            "",
            f"- gt.json files: **{gold.get('gt_files')}**",
            f"- labels: `{json.dumps(gold.get('by_label'), ensure_ascii=False)}`",
            f"- variants: `{json.dumps(gold.get('by_variant'), ensure_ascii=False)}`",
            f"- Harbor agent: **{harbor.get('status')}**",
            f"- sheets on disk: **{(payload.get('assets') or {}).get('pdf_files')}** / "
            f"{(payload.get('assets') or {}).get('manifest_pdf_urls')} manifest PDFs",
            f"- null_always_clean false_positive: **{null.get('false_positive')}**",
            f"- null_always_clean true_negative: **{null.get('true_negative')}**",
            f"- null_always_clean false_pass_rate_on_labeled: **{null.get('false_pass_rate_on_labeled')}**",
            f"- labeled_compliance_tasks: **{null.get('labeled_compliance_tasks')}**",
            "",
            "Harbor drawing-reading false-pass remains **NOT_MEASURED**. "
            "The Yandex Studio key already ran **AECV-Bench** counting "
            "(macro_extended=0.4325, 2026-08-04); Harbor is a different "
            "Codex/Claude agent and does not take that key. "
            "`null_always_clean` is a gold-only floor: always say compliant, never open a sheet. "
            "Not AeroBIM product accuracy. Not RT-001. Observation unit = task, not project cluster.",
            "",
            "```bash",
            "cd backend",
            "python -m aerobim.tools.run_aec_bench_smoke --also-docs-evidence",
            "```",
            "",
        ]
    )


def _write_false_pass_evidence(repo: Path, smoke: dict[str, Any]) -> None:
    gold = smoke.get("gold") or {}
    null = gold.get("null_always_clean") or {}
    body = {
        "artifact_type": "aec_bench_false_pass",
        "schema_version": "1.1.0",
        "generated_at": smoke.get("generated_at"),
        "claim_level": "open_bench_only",
        "closes_rt001": False,
        "customer_accuracy_not_established": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "benchmark": {
            "name": "AEC-Bench",
            "arxiv": "2603.29199",
            "mushkani_subset_arxiv": "2607.29058",
            "inventory_tasks": (smoke.get("benchmark") or {}).get("instance_count"),
            "gold_files": gold.get("gt_files"),
            "observation_unit_gold": "task",
            "observation_unit_mushkani": "project",
        },
        "false_pass": {
            "status": "NOT_MEASURED",
            "reason": (
                "Harbor Codex/Claude trial NOT_RUN (needs OpenAI/Anthropic agent key + Docker). "
                "Yandex Studio key is a different contour: it already scored AECV-Bench counting, "
                "not this Harbor agent. null_always_clean is gold-only."
            ),
        },
        "null_always_clean": null,
        "gold": {
            "status": gold.get("status"),
            "by_label": gold.get("by_label"),
            "by_variant": gold.get("by_variant"),
        },
        "cluster_bootstrap": {"status": "NOT_MEASURED"},
        "four_outcome_table": {
            "status": "NULL_BASELINE_ONLY",
            "true_positive": null.get("true_positive"),
            "false_positive": null.get("false_positive"),
            "true_negative": null.get("true_negative"),
            "false_negative": null.get("false_negative"),
        },
    }
    encoded = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    body["content_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    text = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    (repo / "docs" / "evidence" / "aec-bench-false-pass-2026-08.json").write_text(
        text, encoding="utf-8"
    )
    (repo / "docs" / "evidence" / "aec-bench-false-pass-2026-08.md").write_text(
        render_false_pass_markdown(smoke), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument(
        "--prefetch",
        action="store_true",
        help="Download manifest assets for --scope/--family/--instance",
    )
    parser.add_argument("--scope", default="intrasheet", help="intrasheet|intradrawing|intraproject|all")
    parser.add_argument("--family", default=None)
    parser.add_argument("--instance", default=None)
    parser.add_argument("--prefetch-limit", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--also-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    dataset_root = (args.dataset_root or default_dataset_root()).resolve()
    instances = discover_instances(dataset_root)
    by_scope: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for item in instances:
        by_scope[item["scope"]] = by_scope.get(item["scope"], 0) + 1
        key = f"{item['scope']}/{item['family']}"
        by_family[key] = by_family.get(key, 0) + 1

    prefetch_results: list[dict[str, Any]] = []
    if args.prefetch:
        candidates = [
            i
            for i in instances
            if (args.scope == "all" or i["scope"] == args.scope)
            and (args.family is None or i["family"] == args.family)
            and (args.instance is None or i["instance"] == args.instance)
            and i["has_manifest"]
        ]
        for item in candidates[: max(0, args.prefetch_limit)]:
            prefetch_results.append(
                prefetch_instance(
                    dataset_root,
                    scope=item["scope"],
                    family=item["family"],
                    instance=item["instance"],
                    timeout_s=args.timeout_seconds,
                )
            )

    openai_set = _secret_present("OPENAI_API_KEY")
    anthropic_set = _secret_present("ANTHROPIC_API_KEY")
    yandex_set = _secret_present("AEROBIM_LLM_API_KEY")
    gold = inventory_gold(dataset_root)
    report = {
        "artifact_type": "aec_bench_smoke",
        "schema_version": "1.1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "open_bench_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "closes_rt001": False,
        "benchmark": {
            "name": "AEC-Bench",
            "arxiv": "2603.29199",
            "dataset_root": str(dataset_root),
            "instance_count": len(instances),
            "by_scope": by_scope,
            "by_family": by_family,
        },
        "gold": gold,
        "assets": inventory_pdf_assets(dataset_root),
        "prefetch": prefetch_results,
        "agent_trial": {
            "status": "NOT_RUN",
            "reason": (
                "Harbor is a Codex/Claude Docker agent. It does not take the Yandex "
                "AI Studio Completions key. Yandex key present="
                f"{str(yandex_set).lower()}; that key already ran AECV-Bench live "
                "counting (macro_extended=0.4325 on 2026-08-04). OPENAI_API_KEY/"
                "ANTHROPIC_API_KEY are a different vendor; a prior OpenAI-compat "
                "call returned HTTP 401. Do not paste the Yandex key into Harbor."
            ),
            "yandex_studio_key_present": yandex_set,
            "openai_key_present": openai_set,
            "anthropic_key_present": anthropic_set,
            "harbor_hint": (
                r"%USERPROFILE%\.local\bin\harbor.exe trials start "
                "--path tasks/<scope>/<family>/<instance> "
                "-a aec_bench.agents.codex_agent:CodexAgent -m openai/gpt-4o"
            ),
        },
    }

    out = args.output or (repo_root() / "artifacts" / "open-bench" / "aec-bench-smoke.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    report["output_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report["output_path"] = str(out)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    if args.also_docs_evidence:
        docs_report = json.loads(json.dumps(report, ensure_ascii=False))
        docs_report["prefetch"] = [
            {
                "instance": row.get("instance"),
                "scope": row.get("scope"),
                "family": row.get("family"),
                "status": row.get("status"),
                "ok": sum(
                    1
                    for item in row.get("downloads") or []
                    if item.get("status") in {"cached", "downloaded"}
                ),
                "errors": sum(
                    1 for item in row.get("downloads") or [] if item.get("status") == "error"
                ),
            }
            for row in prefetch_results
        ]
        docs_text = json.dumps(docs_report, ensure_ascii=False, indent=2) + "\n"
        evidence = repo_root() / "docs" / "evidence" / "aec-bench-smoke-latest.json"
        evidence.write_text(docs_text, encoding="utf-8")
        print(f"docs_evidence={evidence}")
        _write_false_pass_evidence(repo_root(), docs_report)

    agent_trial = report["agent_trial"]
    assert isinstance(agent_trial, dict)
    print(
        json.dumps(
            {
                "instances": len(instances),
                "by_scope": by_scope,
                "prefetch": [
                    {"instance": r.get("instance"), "status": r.get("status")}
                    for r in prefetch_results
                ],
                "agent_trial": agent_trial["status"],
                "gold": gold.get("by_label"),
                "null_always_clean": (gold.get("null_always_clean") or {}).get(
                    "false_pass_rate_on_labeled"
                ),
                "assets": report.get("assets"),
                "claim_level": "open_bench_only",
            },
            ensure_ascii=False,
        )
    )
    if any(r.get("status") not in {"ok"} for r in prefetch_results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
