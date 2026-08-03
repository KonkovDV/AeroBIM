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

# Soft floor: tiny binaries may still fail; AECV errors 2000-0008/09/12 were
# WEBP bytes labeled ``.jpg`` sent as ``image/jpeg`` (MIME mismatch → HTTP 400),
# not a pure byte-size gate (downsized JPEG ≈780 B still returned 200).
MIN_IMAGE_BYTES_VENDOR_REJECT = 12 * 1024


def _image_mime(path: Path) -> str:
    """Sniff image MIME; do not trust extension (AECV ships WEBP as ``.jpg``)."""

    head = path.read_bytes()[:32]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "image/gif"
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


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
        biases = [
            (r.predicted - r.expected)
            for r in scored
            if r.predicted is not None and r.expected is not None
        ]
        # Refusal-style miss: model emits 0 while ground truth is positive.
        positive_exp = [r for r in scored if (r.expected or 0) > 0]
        zero_when_positive = [
            r for r in positive_exp if r.predicted == 0
        ]
        zero_pred = [r for r in scored if r.predicted == 0]
        per_field[field] = {
            "n": len(scored),
            "exact_match_rate": (
                round(sum(1 for r in scored if r.exact_match) / len(scored), 4)
                if scored
                else None
            ),
            "mape": round(sum(mape_vals) / len(mape_vals), 4) if mape_vals else None,
            "mean_bias": (
                round(sum(biases) / len(biases), 4) if biases else None
            ),
            "zero_prediction_n": len(zero_pred),
            "zero_pred_when_expected_positive_rate": (
                round(len(zero_when_positive) / len(positive_exp), 4)
                if positive_exp
                else None
            ),
            "zero_pred_when_expected_positive_n": len(zero_when_positive),
            "expected_positive_n": len(positive_exp),
        }
    all_scored = [r for r in field_rows if r.exact_match is not None]
    return {
        "n_field_scores": len(all_scored),
        "macro_exact_match_rate": (
            round(sum(1 for r in all_scored if r.exact_match) / len(all_scored), 4)
            if all_scored
            else None
        ),
        "macro_mape": (
            round(
                sum(r.abs_pct_error for r in all_scored if r.abs_pct_error is not None)
                / max(1, sum(1 for r in all_scored if r.abs_pct_error is not None)),
                4,
            )
            if any(r.abs_pct_error is not None for r in all_scored)
            else None
        ),
        "per_field": per_field,
    }


def rescore_live_plans(plans: list[dict[str, Any]]) -> tuple[dict[str, Any], list[FieldScore]]:
    """Recompute aggregates from stored predicted/expected (no API calls)."""

    field_rows: list[FieldScore] = []
    for plan in plans:
        if plan.get("status") not in {None, "ok"}:
            continue
        predicted = plan.get("predicted")
        expected = plan.get("expected")
        if not isinstance(predicted, dict) or not isinstance(expected, dict):
            continue
        field_rows.extend(score_counts(predicted, expected))
    return _aggregate(field_rows), field_rows


def build_executive_summary(
    *,
    live: dict[str, Any] | None,
    offline: dict[str, Any] | None,
) -> dict[str, Any]:
    """Human-facing Red Team slice: MAPE/bias + published baseline comparison."""

    out: dict[str, Any] = {
        "claim_level": "open_bench_only",
        "closes_rt001": False,
        "note": (
            "MAPE + mean_bias sit beside exact-match. "
            "zero_pred_when_expected_positive ≈ refusal/miss, not symmetric error. "
            "Compare live macro to offline published AECV model JSONs (same 120 plans)."
        ),
        "vendor_min_image_bytes": MIN_IMAGE_BYTES_VENDOR_REJECT,
        "vendor_min_image_note": (
            "AECV errors 2000-0008/09/12 were WEBP payloads with .jpg names "
            "sent as image/jpeg (MIME mismatch → HTTP 400). Sniff magic bytes. "
            "Byte-size alone is not the gate: synthetic JPEG ≈780 B still 200."
        ),
    }
    if isinstance(live, dict):
        summary = live.get("summary") or {}
        per_field = summary.get("per_field") or {}
        out["live"] = {
            "provider": live.get("provider"),
            "model": live.get("model"),
            "plans_attempted": live.get("plans_attempted"),
            "plans_scored": sum(
                1 for p in (live.get("plans") or []) if p.get("status") == "ok"
            ),
            "errors": live.get("errors"),
            "macro_exact_match_rate": summary.get("macro_exact_match_rate"),
            "macro_exact_match_rate_paper_four_fields": (
                round(
                    sum(
                        (per_field.get(f) or {}).get("exact_match_rate") or 0.0
                        for f in ("Door", "Window", "Bedroom", "Toilet")
                    )
                    / 4,
                    4,
                )
                if all(
                    (per_field.get(f) or {}).get("exact_match_rate") is not None
                    for f in ("Door", "Window", "Bedroom", "Toilet")
                )
                else None
            ),
            "macro_four_fields_note": (
                "AECV-Bench paper Table 1 mean is over Door/Window/Bedroom/Toilet only. "
                "AeroBIM five-field macro also includes Space and is not directly comparable."
            ),
            "macro_mape": summary.get("macro_mape"),
            "per_field": {
                field: {
                    "exact_match_rate": (per_field.get(field) or {}).get(
                        "exact_match_rate"
                    ),
                    "mape": (per_field.get(field) or {}).get("mape"),
                    "mean_bias": (per_field.get(field) or {}).get("mean_bias"),
                    "zero_prediction_n": (per_field.get(field) or {}).get(
                        "zero_prediction_n"
                    ),
                    "zero_pred_when_expected_positive_n": (per_field.get(field) or {}).get(
                        "zero_pred_when_expected_positive_n"
                    ),
                    "zero_pred_when_expected_positive_rate": (
                        per_field.get(field) or {}
                    ).get("zero_pred_when_expected_positive_rate"),
                }
                for field in COUNT_FIELDS
            },
            "error_plans": [
                {
                    "plan_id": p.get("plan_id"),
                    "detail": p.get("detail"),
                    "image_bytes": p.get("image_bytes"),
                }
                for p in (live.get("plans") or [])
                if p.get("status") == "error"
            ],
        }
        # Window vs Space: same exact can hide different failure modes.
        win = per_field.get("Window") or {}
        space = per_field.get("Space") or {}
        out["failure_mode_contrast"] = {
            "Window": {
                "exact_match_rate": win.get("exact_match_rate"),
                "mape": win.get("mape"),
                "mean_bias": win.get("mean_bias"),
                "reading": "systematic undercount when mean_bias << 0",
            },
            "Space": {
                "exact_match_rate": space.get("exact_match_rate"),
                "mape": space.get("mape"),
                "mean_bias": space.get("mean_bias"),
                "reading": "near-zero bias ⇒ symmetric misses despite low exact",
            },
        }

    if isinstance(offline, dict) and isinstance(offline.get("models"), dict):
        ranked = sorted(
            offline["models"].items(),
            key=lambda kv: -(kv[1].get("macro_exact_match_rate") or -1.0),
        )
        top = [
            {
                "model": name,
                "macro_exact_match_rate": payload.get("macro_exact_match_rate"),
                "macro_mape": payload.get("macro_mape"),
                "Door_exact": (payload.get("per_field") or {})
                .get("Door", {})
                .get("exact_match_rate"),
                "Window_exact": (payload.get("per_field") or {})
                .get("Window", {})
                .get("exact_match_rate"),
                "Bedroom_exact": (payload.get("per_field") or {})
                .get("Bedroom", {})
                .get("exact_match_rate"),
            }
            for name, payload in ranked[:8]
        ]
        live_macro = None
        if isinstance(live, dict):
            live_macro = (live.get("summary") or {}).get("macro_exact_match_rate")
        best = top[0] if top else None
        out["published_baseline_comparison"] = {
            "source": "offline rescore of AECV-Bench per-plan published model JSONs",
            "plans_scored": offline.get("plans_scored"),
            "top_published": top,
            "live_vs_best_published": {
                "live_macro_exact_match_rate": live_macro,
                "best_published_model": (best or {}).get("model"),
                "best_published_macro_exact_match_rate": (best or {}).get(
                    "macro_exact_match_rate"
                ),
                "delta_live_minus_best": (
                    round(live_macro - best["macro_exact_match_rate"], 4)
                    if live_macro is not None
                    and best
                    and best.get("macro_exact_match_rate") is not None
                    else None
                ),
                "reading": (
                    "Live Qwen macro in the same ballpark as mid/frontier published "
                    "counting scores ⇒ harness plausible; large positive gap would "
                    "implicate prompt/resolution, not just model class."
                ),
            },
        }
    return out


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
    mime = _image_mime(image_path)
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
        image_path = images[0]
        image_bytes = image_path.stat().st_size
        expected = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        if image_bytes < MIN_IMAGE_BYTES_VENDOR_REJECT:
            errors += 1
            per_plan.append(
                {
                    "plan_id": folder.name,
                    "status": "error",
                    "detail": (
                        f"preflight_skip_image_bytes<{MIN_IMAGE_BYTES_VENDOR_REJECT}"
                    ),
                    "image_bytes": image_bytes,
                }
            )
            continue
        try:
            predicted = _call_openai_vision_counts(
                image_path=image_path,
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
                    "image_bytes": image_bytes,
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
                    "image_bytes": image_bytes,
                }
            )

    return {
        "task": "object_counting",
        "mode": "live_vision",
        "provider": provider_label,
        "model": model,
        "base_url": base_url,
        "folder_id_set": bool(folder_id),
        "min_image_bytes_vendor_reject": MIN_IMAGE_BYTES_VENDOR_REJECT,
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
    enrich_live_from: Path | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_type": "aecv_bench_eval",
        "schema_version": "1.1.0",
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
    if mode in {"offline", "both", "enrich"}:
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
    if mode == "enrich":
        if enrich_live_from is None or not enrich_live_from.is_file():
            raise SystemExit("--enrich-live-from PATH required for --mode enrich")
        prior = json.loads(enrich_live_from.read_text(encoding="utf-8"))
        live = prior.get("object_counting_live")
        if not isinstance(live, dict) or not isinstance(live.get("plans"), list):
            raise SystemExit("enrich source missing object_counting_live.plans")
        summary, _rows = rescore_live_plans(live["plans"])
        live = dict(live)
        live["summary"] = summary
        live["min_image_bytes_vendor_reject"] = MIN_IMAGE_BYTES_VENDOR_REJECT
        live["enriched_at"] = datetime.now(tz=UTC).isoformat()
        live["enriched_from"] = str(enrich_live_from.resolve())
        # Attach image_bytes for known tiny failures when dataset present.
        root = counting_dir(dataset_root)
        for plan in live["plans"]:
            if plan.get("status") != "error":
                continue
            if plan.get("image_bytes") is not None:
                continue
            folder = root / str(plan.get("plan_id") or "")
            if not folder.is_dir():
                continue
            images = sorted(
                p
                for p in folder.iterdir()
                if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
            )
            if images:
                plan["image_bytes"] = images[0].stat().st_size
        payload["object_counting_live"] = live
        if "drawing_qa" in prior and isinstance(prior["drawing_qa"], dict):
            payload["drawing_qa"] = prior["drawing_qa"]

    payload["executive_summary"] = build_executive_summary(
        live=payload.get("object_counting_live")
        if isinstance(payload.get("object_counting_live"), dict)
        else None,
        offline=payload.get("object_counting_offline")
        if isinstance(payload.get("object_counting_offline"), dict)
        else None,
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=None)
    parser.add_argument(
        "--mode",
        choices=("offline", "live", "both", "enrich"),
        default="offline",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max plans (offline/live)")
    parser.add_argument("--live-model", default="gpt-4o-mini")
    parser.add_argument("--live-base-url", default="https://api.openai.com/v1")
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument(
        "--enrich-live-from",
        type=Path,
        default=None,
        help="With --mode enrich: recompute MAPE/bias + offline compare from saved live plans (no API spend)",
    )
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
        enrich_live_from=args.enrich_live_from,
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
