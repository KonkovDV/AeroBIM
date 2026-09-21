"""Inventory of where package bytes and durable analyze jobs live.

Not a 152-FZ legal opinion. Checkpoint GO; customer_go false.
Not registered in the operator catalog (cap ≤40).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT, checkpoint_fields
from aerobim.infrastructure.adapters.ifc_file_open import ifc_cache_ram_ceiling_payload
from aerobim.tools._cli_base import run_cli


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def build_payload(*, generated_at: str | None = None) -> dict[str, object]:
    ceiling = ifc_cache_ram_ceiling_payload()
    payload: dict[str, object] = {
        "schema_version": "1.1.0",
        "artifact_type": "aerobim_data_residency_inventory",
        "claim_level": "code_inventory",
        "claim_boundary": (
            "Surfaces from Settings env and the JOB-01 worker implementation. "
            "Not a 152-FZ audit or a formally verified per-job sandbox. "
            "Checkpoint GO (regulatory_measurement_mvp; customer_go false)."
        ),
    }
    payload.update(checkpoint_fields())
    payload.update(
        {
            "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
            "closes_rt001": False,
            "surfaces": [
                {
                    "id": "object_store",
                    "kind": "local_disk_or_s3",
                    "path_env": "AEROBIM_STORAGE_DIR",
                    "default": "var/reports",
                    "durable": True,
                },
                {
                    "id": "sqlite_optional",
                    "kind": "local_or_network_db",
                    "path_env": "AEROBIM_DB_URL",
                    "default": None,
                    "durable": True,
                    "required": False,
                },
                {
                    "id": "report_ttl",
                    "kind": "retention_policy",
                    "path_env": "AEROBIM_REPORT_TTL_DAYS",
                    "default": None,
                    "durable": False,
                },
                {
                    "id": "ifc_disk_touch_markers",
                    "kind": "local_disk",
                    "path_env": "AEROBIM_IFC_PARSE_CACHE_DIR",
                    "default": None,
                    "durable": True,
                    "required": False,
                },
                {
                    "id": "ifc_ram_lru",
                    "kind": "worker_process_memory",
                    "config": "max_cached_models × max_ifc_bytes",
                    "max_cached_models": ceiling["max_cached_models"],
                    "max_bytes_per_cached_model": ceiling["max_bytes_per_model"],
                    "durable": False,
                },
                {
                    "id": "redis_control_plane",
                    "kind": "durable_job_store_and_reliable_queue",
                    "path_env": "AEROBIM_REDIS_URL",
                    "default": None,
                    "durable": True,
                    "required_outside_dev": True,
                },
            ],
            "job_queue": {
                "id": "JOB-01",
                "status": "dedicated_durable_worker",
                "durable_workers_claimed": True,
                "delivery": "at_least_once",
                "payload_format": "json",
                "reservation": "redis_brpoplpush_ready_to_processing",
                "ack": "terminal_state_only",
                "honesty": (
                    "Production HTTP is producer-only; aerobim.worker is the executor. "
                    "Redis retains the JSON payload until terminal ACK. Job-store CAS, "
                    "lease ownership and fencing reject duplicate claims or commits. "
                    "Container limits are an isolation boundary, not a formally verified "
                    "fresh per-job sandbox. Exact OOMKilled attribution remains with the runtime."
                ),
                "code_refs": [
                    "backend/src/aerobim/presentation/http/routes/analyze.py",
                    "backend/src/aerobim/infrastructure/adapters/redis_analyze_job_queue.py",
                    "backend/src/aerobim/worker.py",
                    "docker-compose.production.yml",
                ],
            },
            "checkpoint": CHECKPOINT,
        }
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--write-docs-evidence", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    root = repo_root()
    out = args.output
    if args.write_docs_evidence:
        out = root / "docs" / "evidence" / "data-residency-inventory-latest.json"
    if out is None:
        raise SystemExit("pass --output or --write-docs-evidence")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(lambda: main()))
