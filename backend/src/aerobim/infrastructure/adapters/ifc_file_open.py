"""Process-local IFC open helper with optional disk touch markers for SLA.

When ``AEROBIM_IFC_PARSE_CACHE_DIR`` is configured via ``configure_ifc_parse_cache``,
repeated opens of the same path+mtime+size reuse the in-memory model and write a
small marker under the cache dir (observability for package SLA). Never claims
customer ≤30 min.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.ifc_spatial_index import IfcSpatialIndex

_lock = threading.Lock()
_memory: dict[tuple[str, int, int], Any] = {}
_index_memory: dict[tuple[str, int, int], IfcSpatialIndex] = {}
_cache_dir: Path | None = None
_stats: dict[str, int] = {"opens": 0, "hits": 0, "misses": 0, "indexes_built": 0}


@dataclass(frozen=True)
class IfcParseSession:
    """Cached IFC model + spatial index for deterministic_validation hot path."""

    model: Any
    spatial_index: IfcSpatialIndex
    cache_hit: bool
    ifc_path: Path


def configure_ifc_parse_cache(cache_dir: str | Path | None) -> None:
    """Wire from bootstrap when Settings.ifc_parse_cache_dir is set."""

    global _cache_dir
    with _lock:
        if cache_dir is None or str(cache_dir).strip() == "":
            _cache_dir = None
            return
        path = Path(cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        _cache_dir = path


def reset_ifc_parse_cache_for_tests() -> None:
    """Clear memory + config (unit tests only)."""

    global _cache_dir
    with _lock:
        _memory.clear()
        _index_memory.clear()
        _cache_dir = None
        for key in _stats:
            _stats[key] = 0


def ifc_parse_cache_stats() -> dict[str, int]:
    """Process-local cache counters for profiling — not customer SLA evidence."""

    with _lock:
        return dict(_stats)


def open_ifc_session(ifc_path: Path) -> IfcParseSession:
    """Open IFC with memoized model and spatial index."""

    resolved = ifc_path.resolve()
    stat = resolved.stat()
    key = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))
    with _lock:
        model_cache_hit = key in _memory
        cached_index = _index_memory.get(key)
    model = open_ifc_model(ifc_path)
    if cached_index is None:
        cached_index = IfcSpatialIndex.from_model(model)
        with _lock:
            _index_memory[key] = cached_index
            _stats["indexes_built"] += 1
    return IfcParseSession(
        model=model,
        spatial_index=cached_index,
        cache_hit=model_cache_hit,
        ifc_path=resolved,
    )


def open_ifc_model(ifc_path: Path) -> Any:
    """Open IFC via ifcopenshell with process-local memoization."""

    try:
        import ifcopenshell
    except ModuleNotFoundError as exc:
        raise RuntimeError("ifcopenshell is required to open IFC models") from exc

    resolved = ifc_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    stat = resolved.stat()
    key = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))
    with _lock:
        cached = _memory.get(key)
        if cached is not None:
            _touch_marker(resolved, hit=True)
            _stats["opens"] += 1
            _stats["hits"] += 1
            return cached
        _stats["opens"] += 1
        _stats["misses"] += 1
    model = ifcopenshell.open(str(resolved))
    with _lock:
        _memory[key] = model
        _touch_marker(resolved, hit=False)
    return model


def _touch_marker(ifc_path: Path, *, hit: bool) -> None:
    if _cache_dir is None:
        return
    digest = hashlib.sha256(str(ifc_path).encode("utf-8")).hexdigest()[:16]
    marker = _cache_dir / f"{digest}.json"
    payload = {
        "path": str(ifc_path),
        "cache_hit": hit,
        "touched_at": datetime.now(UTC).isoformat(),
        "claim_boundary": "NFR observability only — not customer SLA evidence",
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
