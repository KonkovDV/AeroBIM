"""Reconcile uncommitted audit orphans (RT-HYPER storage recovery).

Scans ``storage_dir/orphans/*.json`` written when ``FilesystemAuditStore.save``
fails after artifact materialization. Dry-run by default; ``--apply`` deletes
recorded artifact keys / drawing-asset dirs and removes orphan records when the
report is still uncommitted.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore


def reconcile_orphans(
    storage_dir: Path,
    *,
    object_store: LocalObjectStore | None = None,
    apply: bool = False,
) -> dict[str, object]:
    orphan_dir = storage_dir / "orphans"
    reports_dir = storage_dir / "reports"
    store = object_store or LocalObjectStore(storage_dir)
    records: list[dict[str, object]] = []
    if orphan_dir.exists():
        for path in sorted(orphan_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                records.append(
                    {
                        "orphan_file": str(path),
                        "status": "corrupt_orphan_record",
                        "error": str(exc),
                    }
                )
                continue
            report_id = str(payload.get("report_id") or path.stem)
            committed = (reports_dir / f"{report_id}.committed.json").exists()
            report_exists = (reports_dir / f"{report_id}.json").exists()
            artifact_keys = [str(k) for k in (payload.get("artifact_keys") or [])]
            entry: dict[str, object] = {
                "report_id": report_id,
                "orphan_file": str(path),
                "committed": committed,
                "report_exists": report_exists,
                "artifact_keys": artifact_keys,
                "consistency_state": payload.get("consistency_state"),
            }
            if committed and report_exists:
                entry["status"] = "resolved_committed"
                if apply:
                    path.unlink(missing_ok=True)
                    entry["orphan_record_removed"] = True
            elif apply and not committed:
                deleted: list[str] = []
                failed: list[str] = []
                for key in artifact_keys:
                    try:
                        store.delete(key)
                        deleted.append(key)
                    except Exception as exc:  # noqa: BLE001 — best-effort cleanup
                        failed.append(f"{key}:{exc}")
                assets = storage_dir / "drawing-assets" / report_id
                if assets.exists():
                    try:
                        shutil.rmtree(assets)
                        entry["drawing_assets_removed"] = True
                    except OSError as exc:
                        failed.append(f"drawing-assets:{exc}")
                path.unlink(missing_ok=True)
                entry["status"] = "cleaned_uncommitted"
                entry["deleted_keys"] = deleted
                entry["failed"] = failed
                entry["orphan_record_removed"] = True
            else:
                entry["status"] = "orphan_uncommitted"
            records.append(entry)

    return {
        "artifact_type": "aerobim_orphan_reconciliation",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "storage_dir": str(storage_dir),
        "apply": apply,
        "orphan_count": len(records),
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete orphan artifacts and remove orphan records (default: dry-run)",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=Path("var/reports"),
        help="Audit storage directory (default: var/reports)",
    )
    args = parser.parse_args(argv)
    storage_dir = args.storage_dir.resolve()
    payload = reconcile_orphans(
        storage_dir,
        object_store=LocalObjectStore(storage_dir),
        apply=args.apply,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
