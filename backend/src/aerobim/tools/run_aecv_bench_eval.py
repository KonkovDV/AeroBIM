"""AECV-Bench evaluation (object counting + optional live vision).

``claim_level=open_bench_only`` — never product accuracy / RT-001.

Modes:
- ``offline``: re-score published per-folder model JSONs vs ``metadata.json``
  on the local AECV-Bench checkout (120 plans).
- ``live``: call OpenAI-compatible vision API on floor-plan PNGs and score
  the same fields (Door/Window/Space/Bedroom/Toilet).

Requires dataset at ``AEROBIM_AECV_BENCH_ROOT`` or ``.local/AECV-Bench``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "AECV-Bench open_bench_only (arXiv:2601.04819). Drawing-literacy baseline "
    "on public floor plans. NOT AeroBIM product accuracy. Never >90% as product. "
    "Does not close RT-001."
)

COUNT_FIELDS = ("Door", "Window", "Space", "Bedroom", "Toilet")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def default_dataset_root() -> Path:
    env = (os.getenv("AEROBIM_AECV_BENCH_ROOT") or "").strip()
    if env:
        return Path(env)
    return repo_root() / ".local" / "AECV-Bench"


def counting_dir(dataset_root: Path) -> Path:
    return (
        dataset_root
        / "data"
        / "Use Case 1 - Object Counting"
        / "1 - Full Datasets"
    )


@dataclass(frozen=True)
class FieldScore:
    field: str
    predicted: int | None
    expected: int | None
    exact_match: bool | None
    abs_pct_error: float | None


def _mape_one(pred: int | None, exp: int | None) -> float | None:
    if pred is None or exp is None:
        return None
    if exp == 0:
        return 0.0 if pred == 0 else 1.0
    return abs(pred - exp) / abs(exp)


def score_counts(
    predicted: dict[str, Any], expected: dict[str, Any]
) -> list[FieldScore]:
    out: list[FieldScore] = []
    for field in COUNT_FIELDS:
        exp_raw = expected.get(field)
        pred_raw = predicted.get(field)
        try:
            exp = int(exp_raw) if exp_raw is not None and exp_raw != "-" else None
        except (TypeError, ValueError):
            exp = None
        try:
            pred = int(pred_raw) if pred_raw is not None and pred_raw != "-" else None
        except (TypeError, ValueError):
            pred = None
        exact = None if exp is None or pred is None else pred == exp
        out.append(
            FieldScore(
                field=field,
                predicted=pred,
                expected=exp,
                exact_match=exact,
                abs_pct_error=_mape_one(pred, exp),
            )
        )
    return out


def _aggregate(field_rows: list[FieldScore]) -> dict[str, Any]:
    by_field: dict[str, list[FieldScore]] = {f: [] for f in COUNT_FIELDS}
    for row in field_rows:
        by_field[row.field].append(row)
    per_field: dict[str, Any] = {}
    for field, rows in by_field.items():
        scored = [r for r in rows if r.exact_match is not None]
        mape_vals = [r.abs_pct_error for r in scored if r.abs_pct_error is not None]
        per_field[field] = {
            "n": len(scored),
            "exact_match_rate": (
                round(sum(1 for r in scored if r.exact_match) / len(scored), 4)
                if scored
                else None
            ),
            "mape": round(sum(mape_vals) / len(mape_vals), 4) if mape_vals else None,
        }
    all_scored = [r for r in field_rows if r.exact_match is not None]
    return {
        "n_field_scores": len(all_scored),
        "macro_exact_match_rate": (
            round(sum(1 for r in all_scored if r.exact_match) / len(all_scored), 4)
            if all_scored
            else None
        ),
        "per_field": per_field,
    }


def evaluate_offline_counting(
    dataset_root: Path, *, limit: int | None = None
) -> dict[str, Any]:
    root = counting_dir(dataset_root)
    if not root.is_dir():
        raise FileNotFoundError(f"AECV counting dataset missing: {root}")

    folders = sorted(p for p in root.iterdir() if p.is_dir())
    if limit is not None:
        folders = folders[: max(0, limit)]

    models: dict[str, list[FieldScore]] = {}
    plans_scored = 0
    for folder in folders:
        meta_path = folder / "metadata.json"
        if not meta_path.is_file():
            continue
        expected = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        plans_scored += 1
        for pred_path in folder.glob("*.json"):
            if pred_path.name == "metadata.json":
                continue
            try:
                predicted = json.loads(pred_path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                continue
            if not isinstance(predicted, dict):
                continue
            # Skip schema-only dumps (have nested properties).
            if "properties" in predicted and not any(f in predicted for f in COUNT_FIELDS):
                continue
            if not any(f in predicted for f in COUNT_FIELDS):
                continue
            model = pred_path.stem
            models.setdefault(model, []).extend(score_counts(predicted, expected))

    model_summaries = {
        name: _aggregate(rows) for name, rows in sorted(models.items())
    }
    # Highlight symbol-hard fields (Door/Window) vs Bedroom/Toilet.
    return {
        "task": "object_counting",
        "mode": "offline_rescore_published_predictions",
        "plans_scored": plans_scored,
        "models": model_summaries,
        "literature_note": (
            "AECV-Bench reports OCR-strong / symbol-counting weak; "
            "compare Door/Window exact_match_rate vs Bedroom/Toilet."
        ),
    }


def _openai_key() -> str | None:
    return (os.getenv("OPENAI_API_KEY") or "").strip() or None


def _yandex_settings() -> dict[str, str] | None:
    """Prefer AeroBIM Yandex Studio env if API key is present."""

    key = (os.getenv("AEROBIM_LLM_API_KEY") or "").strip()
    if not key:
        return None
    folder = (os.getenv("AEROBIM_LLM_FOLDER_ID") or "").strip()
    base = (
        os.getenv("AEROBIM_LLM_BASE_URL") or "https://llm.api.cloud.yandex.net/v1"
    ).strip()
    model = (os.getenv("AEROBIM_LLM_MODEL") or "").strip()
    if not model and folder:
        model = f"gpt://{folder}/qwen3.6-35b-a3b"
    if not model:
        return None
    scheme = (os.getenv("AEROBIM_LLM_AUTH_SCHEME") or "Api-Key").strip() or "Api-Key"
    return {
        "api_key": key,
        "base_url": base,
        "model": model,
        "folder_id": folder,
        "auth_scheme": scheme,
    }


def _call_openai_vision_counts(
    *,
    image_path: Path,
    model: str,
    api_key: str,
    base_url: str,
    timeout_s: float,
    folder_id: str | None = None,
    auth_scheme: str = "Bearer",
) -> dict[str, Any]:
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    suffix = image_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    prompt = (
        "Count elements on this architectural floor plan. "
        "Return ONLY a JSON object with integer keys: "
        "Door, Window, Space, Bedroom, Toilet. "
        "Door/Window = total of all types. "
        "Space = every enclosed room/area. "
        "Bedroom/Toilet = rooms of those types."
    )
    body: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
    }
    # Yandex Qwen3.6: top-level enable_thinking/extra_body → 400;
    # chat_template_kwargs.enable_thinking=false returns content (not reasoning_only).
    if "yandex" in base_url.lower() or model.startswith("gpt://"):
        body["chat_template_kwargs"] = {"enable_thinking": False}
    auth_header = (
        f"Api-Key {api_key}"
        if auth_scheme.lower() in {"api-key", "api_key", "apikey"}
        else f"Bearer {api_key}"
    )
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }
    if folder_id:
        headers["x-folder-id"] = folder_id
        headers["x-data-logging-enabled"] = "false"
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    text = str(content or "").strip()
    if not text:
        # Thinking models may park output in reasoning_content.
        message = payload["choices"][0]["message"]
        text = str(message.get("reasoning_content") or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def evaluate_live_counting(
    dataset_root: Path,
    *,
    limit: int,
    model: str,
    base_url: str,
    timeout_s: float,
) -> dict[str, Any]:
    yandex = _yandex_settings()
    if yandex is not None:
        api_key = yandex["api_key"]
        base_url = yandex["base_url"]
        model = yandex["model"]
        folder_id = yandex["folder_id"] or None
        auth_scheme = yandex["auth_scheme"]
        provider_label = "yandex-ai-studio"
    else:
        api_key = _openai_key()
        if not api_key:
            raise RuntimeError(
                "No live credentials: set AEROBIM_LLM_API_KEY (+ FOLDER_ID/MODEL) "
                "for Yandex Studio, or OPENAI_API_KEY for OpenAI vision"
            )
        folder_id = None
        auth_scheme = "Bearer"
        provider_label = "openai_compat"

    root = counting_dir(dataset_root)
    folders = sorted(p for p in root.iterdir() if p.is_dir())[: max(0, limit)]
    field_rows: list[FieldScore] = []
    per_plan: list[dict[str, Any]] = []
    errors = 0

    for folder in folders:
        meta_path = folder / "metadata.json"
        images = sorted(
            [
                p
                for p in folder.iterdir()
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
            ]
        )
        if not meta_path.is_file() or not images:
            continue
        expected = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        try:
            predicted = _call_openai_vision_counts(
                image_path=images[0],
                model=model,
                api_key=api_key,
                base_url=base_url,
                timeout_s=timeout_s,
                folder_id=folder_id,
                auth_scheme=auth_scheme,
            )
            scores = score_counts(predicted, expected)
            field_rows.extend(scores)
            per_plan.append(
                {
                    "plan_id": folder.name,
                    "predicted": predicted,
                    "expected": expected,
                    "field_exact": {
                        s.field: s.exact_match for s in scores
                    },
                    "status": "ok",
                }
            )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as exc:
            errors += 1
            per_plan.append(
                {
                    "plan_id": folder.name,
                    "status": "error",
                    "detail": str(exc)[:300],
                }
            )

    return {
        "task": "object_counting",
        "mode": "live_vision",
        "provider": provider_label,
        "model": model,
        "base_url": base_url,
        "folder_id_set": bool(folder_id),
        "plans_attempted": len(per_plan),
        "errors": errors,
        "summary": _aggregate(field_rows),
        "plans": per_plan,
    }


def evaluate_qa_labels_inventory(dataset_root: Path) -> dict[str, Any]:
    labels_dir = (
        dataset_root
        / "data"
        / "Use Case 2 - Drawing Understanding"
        / "01 - Full Dataset"
        / "labels"
    )
    if not labels_dir.is_dir():
        return {"task": "drawing_qa", "status": "missing_labels"}
    labels = sorted(labels_dir.glob("*.json"))
    by_task: dict[str, int] = {}
    total_qa = 0
    for path in labels:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for key in ("ocr_qa", "spatial_qa", "counting_qa", "comparative_qa"):
            items = data.get(key) or []
            if not isinstance(items, list):
                continue
            by_task[key] = by_task.get(key, 0) + len(items)
            total_qa += len(items)
    result_csvs = sorted(
        (dataset_root / "benchmark_result_qa").glob("qa_results_*.csv")
    )
    return {
        "task": "drawing_qa",
        "mode": "inventory_plus_published_result_csvs",
        "label_files": len(labels),
        "total_qa_pairs": total_qa,
        "qa_pairs_by_bucket": by_task,
        "published_result_csvs": [p.name for p in result_csvs],
        "note": (
            "Full LLM-as-a-judge re-score deferred; published CSVs present for "
            "offline audit. Live QA vision can be added with --mode live-qa."
        ),
    }


def build_report(
    dataset_root: Path,
    *,
    mode: str,
    limit: int | None,
    live_model: str,
    live_base_url: str,
    timeout_s: float,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_type": "aecv_bench_eval",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "open_bench_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "closes_rt001": False,
        "benchmark": {
            "name": "AECV-Bench",
            "arxiv": "2601.04819",
            "dataset_root": str(dataset_root.resolve()),
        },
        "drawing_qa": evaluate_qa_labels_inventory(dataset_root),
    }
    if mode in {"offline", "both"}:
        payload["object_counting_offline"] = evaluate_offline_counting(
            dataset_root, limit=limit
        )
    if mode in {"live", "both"}:
        live_limit = 10 if limit is None else limit
        payload["object_counting_live"] = evaluate_live_counting(
            dataset_root,
            limit=live_limit,
            model=live_model,
            base_url=live_base_url,
            timeout_s=timeout_s,
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument(
        "--mode",
        choices=("offline", "live", "both"),
        default="offline",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max plans (offline/live)")
    parser.add_argument("--live-model", default="gpt-4o-mini")
    parser.add_argument("--live-base-url", default="https://api.openai.com/v1")
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--also-docs-evidence", action="store_true")
    args = parser.parse_args(argv)

    dataset_root = (args.dataset_root or default_dataset_root()).resolve()
    if not dataset_root.is_dir():
        raise SystemExit(f"Dataset root missing: {dataset_root}")

    report = build_report(
        dataset_root,
        mode=args.mode,
        limit=args.limit,
        live_model=args.live_model,
        live_base_url=args.live_base_url,
        timeout_s=args.timeout_seconds,
    )
    out = args.output or (
        repo_root() / "artifacts" / "open-bench" / "aecv-bench-eval.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    report["output_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report["output_path"] = str(out)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    if args.also_docs_evidence:
        evidence = repo_root() / "docs" / "evidence" / "aecv-bench-eval-latest.json"
        evidence.write_text(text, encoding="utf-8")
        print(f"docs_evidence={evidence}")

    summary: dict[str, Any] = {"claim_level": "open_bench_only", "output": str(out)}
    offline = report.get("object_counting_offline")
    if isinstance(offline, dict):
        summary["offline_plans"] = offline.get("plans_scored")
        # pick a couple of models for stdout
        models = offline.get("models") or {}
        sample = {
            k: v.get("macro_exact_match_rate")
            for k, v in list(models.items())[:5]
        }
        summary["offline_macro_sample"] = sample
    live = report.get("object_counting_live")
    if isinstance(live, dict):
        summary["live"] = {
            "model": live.get("model"),
            "attempted": live.get("plans_attempted"),
            "errors": live.get("errors"),
            "macro": (live.get("summary") or {}).get("macro_exact_match_rate"),
            "per_field": (live.get("summary") or {}).get("per_field"),
        }
    print(json.dumps(summary, ensure_ascii=False))
    if isinstance(live, dict) and live.get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
