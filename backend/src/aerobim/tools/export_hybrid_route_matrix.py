"""Export the Hybrid AI route matrix as reproducible evidence (P2, Задача 10 #1).

Перечисляет виды данных × цели маршрута × типы задач через
``classify_object -> decide_route -> ModelRouter.select`` и фиксирует итоговый
маршрут, tier модели и флаг внешнего выхода (external egress). Сопутствующий тест
проверяет инвариант безопасности: внешний выход возможен ТОЛЬКО для PUBLIC-маршрута
(класс PUBLIC + цель PUBLIC), а также воспроизводимость этого артефакта.

Fixture/matrix evidence — НЕ точность продукта; контур verdict-neutral; Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.hybrid import (
    DataClassification,
    ModelRouter,
    ProviderRegistry,
    RouteTarget,
    classify_object,
    decide_route,
)

_KINDS: tuple[str, ...] = (
    "ifc",
    "drawing",
    "calculation",
    "customer_corpus",
    "samolet_data",
    "pii",
    "api_key",
    "token",
    "public_fixture",
    "internal_doc",
    "unknown_kind",
)
_TARGETS: tuple[str, ...] = ("local", "private", "public")
_TASKS: tuple[str, ...] = ("drawing_read", "table_read")
_TENANT = "tenant-a"

# Canonical provider config for the matrix (models are placeholders — provider-agnostic).
_CONFIG: dict[str, Any] = {
    "profiles": {
        "local_vlm": {"tier": "local", "provider": "onprem", "model_id": "local-vlm-v1"},
        "private_vlm": {"tier": "private", "provider": "ru-cloud", "model_id": "private-vlm-v1"},
        "public_model": {"tier": "public", "provider": "public-cloud", "model_id": "public-v1"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "expert"},
    },
    "tier_defaults": {"local": "local_vlm", "private": "private_vlm", "public": "public_model"},
    "human_review_profile": "human_review",
}


def _router() -> ModelRouter:
    return ModelRouter(ProviderRegistry.from_config(_CONFIG))


def build_route_matrix() -> dict[str, Any]:
    """Deterministically enumerate the full class×target×task route matrix."""
    router = _router()
    rows: list[dict[str, Any]] = []
    for kind in _KINDS:
        classification = classify_object(kind)
        for target_name in _TARGETS:
            decision = decide_route(
                classification=classification,
                target=RouteTarget(target_name),
                tenant_id=_TENANT,
            )
            for task in _TASKS:
                selection = router.select(decision=decision, task_type=task)
                profile = selection.profile
                rows.append(
                    {
                        "kind": kind,
                        "classification": classification.value,
                        "target": target_name,
                        "task": task,
                        "route_status": decision.status.value,
                        "model_tier": profile.tier.value if profile is not None else None,
                        "external": selection.external,
                        "requires_human_review": selection.requires_human_review,
                    }
                )

    unknown_tenant: list[dict[str, Any]] = []
    for target_name in _TARGETS:
        decision = decide_route(
            classification=DataClassification.PUBLIC,
            target=RouteTarget(target_name),
            tenant_id="",
        )
        selection = router.select(decision=decision, task_type="drawing_read")
        unknown_tenant.append(
            {
                "target": target_name,
                "route_status": decision.status.value,
                "external": selection.external,
            }
        )

    external_rows = [r for r in rows if r["external"]]
    return {
        "artifact": "hybrid-route-matrix",
        "note": (
            "fixture/matrix evidence; not product accuracy; verdict-neutral (OFF==ON); "
            "masking != anonymity; Checkpoint GO (regulatory_measurement_mvp; customer_go false)"
        ),
        "tenant": _TENANT,
        "rows": rows,
        "unknown_tenant": unknown_tenant,
        "summary": {
            "total_cells": len(rows),
            "external_cells": len(external_rows),
            "external_only_for_public_route": all(
                r["classification"] == "public"
                and r["target"] == "public"
                and r["route_status"] == "public_masked"
                and r["model_tier"] == "public"
                for r in external_rows
            ),
            "unknown_tenant_external_cells": sum(1 for r in unknown_tenant if r["external"]),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the Hybrid AI route matrix (evidence).")
    parser.add_argument("--output", type=Path, default=None, help="write JSON here (else stdout)")
    args = parser.parse_args(argv)
    text = json.dumps(build_route_matrix(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
