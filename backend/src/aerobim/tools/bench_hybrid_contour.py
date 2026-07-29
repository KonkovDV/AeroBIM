"""Bench the Hybrid AI contour on synthetic / de-identified cases (P3, БЕЗ внешнего выхода).

Измеряет ТОЛЬКО детерминированный контур: классификация -> маршрут -> обнаружение
сущностей -> маскирование -> **локальное восстановление** -> аудит, плюс объём
исходящих данных (прокси «стоимости») и задержку (wall-clock).

ЧЕСТНЫЕ ГРАНИЦЫ:
- НЕТ ни одного сетевого и ни одного модельного вызова (стенд, не рабочее подключение);
- это НЕ качество модели и НЕ точность продукта (точность вспомогательного разбора
  измеряется отдельно: ``evaluate_drawing_advisory_grounding``);
- задержка зависит от окружения; «стоимость» здесь = байты маскированного payload,
  а не деньги;
- маскирование снижает раскрытие, но НЕ доказывает анонимность;
- вердикт не затрагивается (verdict-neutral), Checkpoint NO_GO.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.domain.hybrid import (
    ModelRouter,
    PrivacyGuard,
    ProviderRegistry,
    RouteTarget,
    suggest_mask_rules,
)

_OTHER_TENANT = "bench-other-tenant"

# Public-enabled provider config so a PUBLIC route CAN select an external profile
# (placeholders only — provider-agnostic, никакой модели не вызывается).
_ROUTER_CONFIG: dict[str, Any] = {
    "profiles": {
        "local_vlm": {"tier": "local", "provider": "onprem", "model_id": "local-bench"},
        "private_vlm": {
            "tier": "private",
            "provider": "private-cloud",
            "model_id": "private-bench",
        },
        "public_vlm": {"tier": "public", "provider": "public-cloud", "model_id": "public-bench"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "expert"},
    },
    "tier_defaults": {"local": "local_vlm", "private": "private_vlm", "public": "public_vlm"},
    "human_review_profile": "human_review",
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", data) if isinstance(data, dict) else data
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"no cases in {path}")
    return [dict(case) for case in cases]


def run_bench(cases: list[dict[str, Any]], *, tenant_salt: str = "bench-salt") -> dict[str, Any]:
    """Run the contour over the case set; return an honest metrics report."""
    guard = PrivacyGuard(tenant_salt=tenant_salt)
    gate = HybridRouteGate(privacy_guard=guard)
    router = ModelRouter(ProviderRegistry.from_config(_ROUTER_CONFIG))

    rows: list[dict[str, Any]] = []
    restore_ok = 0
    restore_total = 0
    cross_tenant_leaks = 0
    raw_leaks = 0
    egress_bytes = 0
    latency_total = 0.0

    for case in cases:
        payload = case.get("payload")
        tenant = str(case.get("tenant", ""))
        rules = suggest_mask_rules(payload, keep_clean_scalars=True) if payload else None

        started = perf_counter()
        result = gate.evaluate(
            object_kind=str(case.get("kind", "unknown")),
            target=RouteTarget(str(case.get("target", "local")).lower()),
            tenant_id=tenant,
            task_type=str(case.get("task", "drawing_read")),
            request_id=f"bench-{case.get('name', 'case')}",
            payload=payload,
            mask_rules=rules,
        )
        selection = router.select(
            decision=result.decision, task_type=str(case.get("task", "drawing_read"))
        )
        latency_ms = (perf_counter() - started) * 1000.0
        latency_total += latency_ms

        masked = result.masked
        blob = json.dumps(masked, ensure_ascii=False) if masked else ""
        egress_bytes += len(blob.encode("utf-8"))

        # Локальное восстановление: токен -> исходное значение только для своего tenant.
        if masked and payload and rules:
            for field, action in rules.items():
                if not action.startswith("tokenize:") or field not in masked:
                    continue
                restore_total += 1
                token = str(masked[field])
                if guard.restore(token, tenant_id=tenant) == str(payload[field]):
                    restore_ok += 1
                if guard.restore(token, tenant_id=_OTHER_TENANT) is not None:
                    cross_tenant_leaks += 1
        # Утечка сырых значений в маскированном payload (должна быть невозможна).
        if masked and payload and rules:
            for field, action in rules.items():
                if action == "keep":
                    continue
                raw = str(payload[field])
                if len(raw) >= 3 and raw in blob:
                    raw_leaks += 1

        rows.append(
            {
                "name": case.get("name"),
                "classification": result.audit_event.classification,
                "route_status": result.decision.status.value,
                "model_tier": selection.profile.tier.value if selection.profile else None,
                "external": result.may_call_external and selection.external,
                "requires_human_review": selection.requires_human_review,
                "fields_sent": list(result.audit_event.fields_sent),
                "fields_removed": list(result.audit_event.fields_removed),
                "egress_bytes": len(blob.encode("utf-8")),
                "verdict_impact": result.audit_event.verdict_impact,
            }
        )

    external_rows = [r for r in rows if r["external"]]
    return {
        "artifact": "hybrid-contour-bench",
        "note": (
            "deterministic contour only; NO network/model call; not model quality and not "
            "product accuracy; latency is environment-specific; masking != anonymity; "
            "verdict-neutral; Checkpoint NO_GO"
        ),
        "rows": rows,
        "summary": {
            "cases": len(rows),
            "external_cases": len(external_rows),
            "external_only_for_public": all(r["classification"] == "public" for r in external_rows),
            "restore_total": restore_total,
            "restore_fidelity": (restore_ok / restore_total) if restore_total else 1.0,
            "cross_tenant_restore_leaks": cross_tenant_leaks,
            "raw_value_leaks": raw_leaks,
            "egress_bytes_total": egress_bytes,
            "verdict_impact_all_none": all(r["verdict_impact"] == "none" for r in rows),
            "latency_ms_total_env_specific": round(latency_total, 3),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bench the Hybrid AI contour (no external output)."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--min-restore-fidelity", type=float, default=None)
    parser.add_argument("--max-raw-leaks", type=int, default=None)
    args = parser.parse_args(argv)

    report = run_bench(load_cases(args.cases))
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)

    summary = report["summary"]
    failed = False
    if (
        args.min_restore_fidelity is not None
        and summary["restore_fidelity"] < args.min_restore_fidelity
    ):
        print(f"restore_fidelity {summary['restore_fidelity']} < {args.min_restore_fidelity}")
        failed = True
    if args.max_raw_leaks is not None and summary["raw_value_leaks"] > args.max_raw_leaks:
        print(f"raw_value_leaks {summary['raw_value_leaks']} > {args.max_raw_leaks}")
        failed = True
    if summary["cross_tenant_restore_leaks"]:
        print(f"cross_tenant_restore_leaks {summary['cross_tenant_restore_leaks']} != 0")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
