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
from typing import Any

CLAIM_BOUNDARY = (
    "AEC-Bench open_bench_only (arXiv:2603.29199). Prefetch/inventory of public "
    "agentic tasks. Agent trial scores are NOT AeroBIM product accuracy and do "
    "not close RT-001."
)


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
                    "sha256": _sha256_file(dest),
                }
            )
            continue
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 AeroBIM-open-bench/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                data = resp.read()
            dest.write_bytes(data)
            downloads.append(
                {
                    "dest": dest_name,
                    "status": "downloaded",
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            downloads.append(
                {
                    "dest": dest_name,
                    "status": "error",
                    "detail": str(exc)[:300],
                }
            )
    ok = all(d.get("status") in {"cached", "downloaded"} for d in downloads)
    return {
        "status": "ok" if ok else "partial_or_failed",
        "scope": scope,
        "family": family,
        "instance": instance,
        "downloads": downloads,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument(
        "--prefetch",
        action="store_true",
        help="Download manifest assets for --scope/--family/--instance",
    )
    parser.add_argument("--scope", default="intrasheet")
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
            if i["scope"] == args.scope
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

    openai_set = bool((os.getenv("OPENAI_API_KEY") or "").strip())
    anthropic_set = bool((os.getenv("ANTHROPIC_API_KEY") or "").strip())
    report = {
        "artifact_type": "aec_bench_smoke",
        "schema_version": "1.0.0",
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
        "prefetch": prefetch_results,
        "agent_trial": {
            "status": "NOT_RUN",
            "reason": (
                "Harbor CLI installed separately; Codex/Claude agent trial needs "
                "valid OPENAI_API_KEY or ANTHROPIC_API_KEY. Live AECV vision returned "
                "HTTP 401 with current OPENAI_API_KEY — do not start paid agent burn "
                "until the key is replaced."
            ),
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
        evidence = repo_root() / "docs" / "evidence" / "aec-bench-smoke-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")

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
