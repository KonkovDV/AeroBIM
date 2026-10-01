"""Process-local IFC open helper with optional disk touch markers for SLA.

When ``AEROBIM_IFC_PARSE_CACHE_DIR`` is configured via ``configure_ifc_parse_cache``,
repeated opens of the same path+mtime+size reuse the in-memory model and write a
small marker under the cache dir (observability for package SLA). Never claims
customer ≤30 min.
"""

from __future__ import annotations

import gc
import hashlib
import json
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.ifc_size_policy import (
    BAND_ANALYZE_DISK,
    SPF_RAM_MULTIPLIER_LITERATURE,
    SPF_RAM_MULTIPLIER_SOURCE,
    IfcDiskBackendError,
    analyze_cap_from_env,
    ingest_cap_from_env,
    literature_spf_rss_bytes,
    raise_if_over_analyze_cap,
)
from aerobim.domain.ifc_spatial_index import IfcSpatialIndex

_DEFAULT_MAX_CACHED_MODELS = 8
# Default 256 MiB (268435456). Comparable to bSI Validation Service 256 MB
# uncompressed .ifc — not the same unit.
_DEFAULT_MAX_BYTES_PER_CACHED_MODEL = 256 * 1024 * 1024


@dataclass
class _CacheEntry:
    model: Any
    refs: int = 0


_lock = threading.Lock()
_memory: OrderedDict[tuple[str, int, int], _CacheEntry] = OrderedDict()
_index_memory: dict[tuple[str, int, int], IfcSpatialIndex] = {}
_inflight: dict[tuple[str, int, int], threading.Event] = {}
_cache_dir: Path | None = None
_max_cached_models = _DEFAULT_MAX_CACHED_MODELS
_stats: dict[str, int] = {
    "opens": 0,
    "hits": 0,
    "misses": 0,
    "indexes_built": 0,
    "evictions": 0,
    "rocksdb_converts": 0,
}


@dataclass(frozen=True)
class IfcParseSession:
    """Cached IFC model + spatial index for deterministic_validation hot path."""

    model: Any
    spatial_index: IfcSpatialIndex
    cache_hit: bool
    ifc_path: Path
    cache_key: tuple[str, int, int] | None = None
    _closed: list[bool] = field(default_factory=lambda: [False], compare=False, repr=False)

    def close(self) -> None:
        if self._closed[0]:
            return
        self._closed[0] = True
        if self.cache_key is not None:
            release_cached_model(self.cache_key)

    def __enter__(self) -> IfcParseSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def configure_ifc_parse_cache(
    cache_dir: str | Path | None,
    *,
    max_models: int | None = None,
) -> None:
    """Wire from bootstrap when Settings.ifc_parse_cache_dir is set."""

    global _cache_dir, _max_cached_models
    with _lock:
        if max_models is not None:
            _max_cached_models = max(1, int(max_models))
        if cache_dir is None or str(cache_dir).strip() == "":
            _cache_dir = None
            return
        path = Path(cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        _cache_dir = path


def reset_ifc_parse_cache_for_tests() -> None:
    """Clear memory + config (unit tests only)."""

    global _cache_dir, _max_cached_models
    with _lock:
        for cached in list(_memory.values()):
            close_ifc_model(cached.model)
        _memory.clear()
        _index_memory.clear()
        _inflight.clear()
        _cache_dir = None
        _max_cached_models = _DEFAULT_MAX_CACHED_MODELS
        for key in _stats:
            _stats[key] = 0
    gc.collect()


def ifc_parse_cache_stats() -> dict[str, int]:
    """Process-local cache counters for profiling — not customer SLA evidence."""

    with _lock:
        return dict(_stats)


def ifc_cache_ram_ceiling_bytes(
    *,
    max_models: int | None = None,
    max_bytes_per_model: int | None = None,
) -> int:
    """Process-local LRU ceiling: max_models × max accepted IFC bytes.

    Not federated-pack RSS, not VM sizing, not customer SLA (RT16-RAM-01).
    """

    models = _DEFAULT_MAX_CACHED_MODELS if max_models is None else max(1, int(max_models))
    per = (
        _DEFAULT_MAX_BYTES_PER_CACHED_MODEL
        if max_bytes_per_model is None
        else max(0, int(max_bytes_per_model))
    )
    return models * per


def ifc_cache_ram_ceiling_payload(
    *,
    max_models: int | None = None,
    max_bytes_per_model: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Honest ceiling record. ``measured_rss_delta_bytes`` stays null until measured."""

    models = _DEFAULT_MAX_CACHED_MODELS if max_models is None else max(1, int(max_models))
    per = (
        _DEFAULT_MAX_BYTES_PER_CACHED_MODEL
        if max_bytes_per_model is None
        else max(0, int(max_bytes_per_model))
    )
    ceiling = ifc_cache_ram_ceiling_bytes(max_models=models, max_bytes_per_model=per)
    return {
        "schema_version": "1.0.0",
        "artifact_type": "ifc_cache_ram_ceiling",
        "generated_at": generated_at,
        "claim_boundary": (
            "Process-local LRU ceiling (max_cached_models × max_ifc_bytes). "
            "Not federated-pack RSS, not VM sizing, not customer SLA. "
            "closes_rt003=false."
        ),
        "max_cached_models": models,
        "max_bytes_per_model": per,
        "ceiling_bytes": ceiling,
        "ceiling_gib": ceiling / (1024**3),
        "measured_rss_delta_bytes": None,
        "representative_scale": False,
        "spf_ram_multiplier_literature": SPF_RAM_MULTIPLIER_LITERATURE,
        "spf_ram_multiplier_source": SPF_RAM_MULTIPLIER_SOURCE,
        "literature_rss_ceiling_bytes": literature_spf_rss_bytes(ceiling),
        "literature_rss_not_measured": True,
        "closes_rt003": False,
        "checkpoint": CHECKPOINT,
    }


def close_ifc_model(model: Any) -> None:
    """Release RocksDB/SPF handles so Windows can delete the store directory."""

    storage = getattr(model, "storage", None)
    for obj in (storage, model):
        if obj is None:
            continue
        closer = getattr(obj, "close", None)
        if callable(closer):
            try:
                closer()
            except Exception:  # noqa: S110 — best-effort handle release
                pass


def _evict_overflow_locked() -> None:
    """Close unreferenced LRU entries only. Pinned (refs>0) models stay open."""

    pinned: list[tuple[tuple[str, int, int], _CacheEntry]] = []
    while len(_memory) > _max_cached_models:
        old_key, entry = _memory.popitem(last=False)
        if entry.refs > 0:
            pinned.append((old_key, entry))
            continue
        _index_memory.pop(old_key, None)
        close_ifc_model(entry.model)
        _stats["evictions"] += 1
    for key, entry in pinned:
        _memory[key] = entry
        _memory.move_to_end(key)


def release_cached_model(key: tuple[str, int, int]) -> None:
    with _lock:
        entry = _memory.get(key)
        if entry is None:
            return
        entry.refs = max(0, entry.refs - 1)


def open_ifc_session(ifc_path: Path) -> IfcParseSession:
    """Open IFC with memoized model and spatial index. Call ``close()`` when done."""

    resolved = ifc_path.resolve()
    stat = resolved.stat()
    key = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))
    with _lock:
        model_cache_hit = key in _memory
        cached_index = _index_memory.get(key)
    model = open_ifc_model(ifc_path, pin=True)
    try:
        with _lock:
            cached_index = _index_memory.get(key)
        if cached_index is None:
            dense = getattr(model, "storage", None) is None
            cached_index = IfcSpatialIndex.from_model(model, dense=dense)
            with _lock:
                _index_memory[key] = cached_index
                _stats["indexes_built"] += 1
        return IfcParseSession(
            model=model,
            spatial_index=cached_index,
            cache_hit=model_cache_hit,
            ifc_path=resolved,
            cache_key=key,
        )
    except Exception:
        release_cached_model(key)
        raise


def ifc_engine_path(ifc_path: Path) -> Path:
    """Path IfcOpenShell/IfcClash should open: SPF file or RocksDB directory.

    Opens (and caches) the model first so convert has already run.
    """

    resolved = ifc_path.resolve()
    model = open_ifc_model(resolved)
    if getattr(model, "storage", None) is None:
        return resolved
    stat = resolved.stat()
    return _rdb_cache_dir(resolved, int(stat.st_mtime_ns), int(stat.st_size))


def rocksdb_backend_available() -> bool:
    """True when this IfcOpenShell build can convert SPF to RocksDB."""

    try:
        import ifcopenshell
    except ModuleNotFoundError:
        return False
    convert = getattr(ifcopenshell, "convert_path_to_rocksdb", None)
    return callable(convert)


def _rdb_cache_dir(ifc_path: Path, mtime_ns: int, size: int) -> Path:
    digest = hashlib.sha256(f"{ifc_path.resolve()}|{mtime_ns}|{size}".encode()).hexdigest()[:16]
    root = _cache_dir if _cache_dir is not None else (ifc_path.parent / ".aerobim-ifc-rdb")
    return Path(root) / digest


def _rdb_ready(path: Path) -> bool:
    return path.is_dir() and (path / "CURRENT").is_file()


def _open_rocksdb(ifc_path: Path, ifcopenshell: Any, mtime_ns: int, size: int) -> Any:
    if not rocksdb_backend_available():
        raise IfcDiskBackendError()
    rdb = _rdb_cache_dir(ifc_path, mtime_ns, size)
    if not _rdb_ready(rdb):
        if rdb.exists():
            import shutil

            shutil.rmtree(rdb, ignore_errors=True)
        rdb.parent.mkdir(parents=True, exist_ok=True)
        try:
            ifcopenshell.convert_path_to_rocksdb(str(ifc_path), str(rdb))
        except Exception as exc:
            import shutil

            shutil.rmtree(rdb, ignore_errors=True)
            raise IfcDiskBackendError() from exc
        with _lock:
            _stats["rocksdb_converts"] += 1
        if not _rdb_ready(rdb):
            raise IfcDiskBackendError()
    try:
        return ifcopenshell.open(str(rdb))
    except Exception as exc:
        raise IfcDiskBackendError() from exc


def open_ifc_model(ifc_path: Path, *, pin: bool = False) -> Any:
    """Open IFC via ifcopenshell with process-local memoization.

    SPF in-memory open stays at ``AEROBIM_MAX_IFC_BYTES`` (default 256 MiB).
    Larger files up to the model ingest envelope use RocksDB. Never SPF-opens
    a file over the in-memory cap.
    """

    try:
        import ifcopenshell

    except ModuleNotFoundError as exc:
        raise RuntimeError("ifcopenshell is required to open IFC models") from exc

    resolved = ifc_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    stat = resolved.stat()
    decision = raise_if_over_analyze_cap(
        int(stat.st_size),
        analyze_cap_bytes=analyze_cap_from_env(),
        ingest_cap_bytes=ingest_cap_from_env(),
    )
    key = (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))
    wait_event: threading.Event | None = None
    we_open = False
    with _lock:
        cached = _memory.get(key)
        if cached is not None:
            _memory.move_to_end(key)
            if pin:
                cached.refs += 1
            _touch_marker(resolved, hit=True)
            _stats["opens"] += 1
            _stats["hits"] += 1
            return cached.model
        inflight = _inflight.get(key)
        if inflight is None:
            wait_event = threading.Event()
            _inflight[key] = wait_event
            we_open = True
        else:
            wait_event = inflight
        _stats["opens"] += 1
        if we_open:
            _stats["misses"] += 1
    if not we_open:
        wait_event.wait()
        with _lock:
            cached = _memory.get(key)
            if cached is not None:
                _memory.move_to_end(key)
                _touch_marker(resolved, hit=True)
                _stats["hits"] += 1
                return cached.model
        raise RuntimeError(f"IFC cache single-flight failed for {resolved}")
    try:
        if decision.band == BAND_ANALYZE_DISK:
            model = _open_rocksdb(resolved, ifcopenshell, int(stat.st_mtime_ns), int(stat.st_size))
        else:
            model = ifcopenshell.open(str(resolved))
        with _lock:
            existing = _memory.get(key)
            if existing is not None:
                close_ifc_model(model)
                if pin:
                    existing.refs += 1
                _memory.move_to_end(key)
                return existing.model
            _memory[key] = _CacheEntry(model=model, refs=1 if pin else 0)
            _memory.move_to_end(key)
            _evict_overflow_locked()
            _touch_marker(resolved, hit=False)
        return model
    finally:
        with _lock:
            event = _inflight.pop(key, None)
            if event is not None:
                event.set()


def _touch_marker(ifc_path: Path, *, hit: bool) -> None:
    if _cache_dir is None:
        return
    digest = hashlib.sha256(str(ifc_path).encode("utf-8")).hexdigest()[:16]
    marker = _cache_dir / f"{digest}.json"
    payload = {
        "path_digest": digest,
        "name": ifc_path.name,
        "cache_hit": hit,
        "touched_at": datetime.now(UTC).isoformat(),
        "claim_boundary": "NFR observability only — not customer SLA evidence",
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
