"""Clash detection adapter using IfcOpenShell + IfcClash.

Raises ``ClashCapabilityError`` when the optional geometry stack is missing or
fails, so callers can record an explicit capability status instead of treating
silent empty results as a clean model.

Tiny / degenerate products (typical schema-suite wall fixtures) often raise a
bare ``AssertionError`` inside IfcClash geom init. Default behaviour skips
those products after a per-element probe so one bad wall does not abort the
whole clash set. Remaining AssertionError still maps to capability failure
(not a silent pass).
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.models import ClashResult

_LOGGER = logging.getLogger(__name__)

DEFAULT_MIN_AABB_VOLUME_M3 = 1e-6


def self_clash_set(ifc_path: Path, *, selector: str | None = None) -> dict[str, Any]:
    """Single-file package: self-clash within set A."""
    source: dict[str, Any] = {"file": str(ifc_path)}
    if selector:
        source["selector"] = selector
    return {
        "name": "Internal hard clashes",
        "mode": "intersection",
        "check_all": True,
        "tolerance": 0.0,
        "a": [source],
    }


def federated_clash_set(
    path_a: Path, path_b: Path, *, selector_a: str | None = None, selector_b: str | None = None
) -> dict[str, Any]:
    """Two-file intersection (architecture vs MEP, etc.). Not system-aware."""
    source_a: dict[str, Any] = {"file": str(path_a)}
    source_b: dict[str, Any] = {"file": str(path_b)}
    if selector_a:
        source_a["selector"] = selector_a
    if selector_b:
        source_b["selector"] = selector_b
    return {
        "name": "Federated hard clashes",
        "mode": "intersection",
        "check_all": True,
        "tolerance": 0.0,
        "a": [source_a],
        "b": [source_b],
    }


def federated_clearance_clash_set(
    path_a: Path,
    path_b: Path,
    *,
    clearance_m: float,
    selector_a: str | None = None,
    selector_b: str | None = None,
) -> dict[str, Any]:
    """Two-file soft clearance (IfcClash mode=clearance). Not MEP system-aware."""
    if clearance_m <= 0:
        raise ValueError("clearance_m must be > 0")
    source_a: dict[str, Any] = {"file": str(path_a)}
    source_b: dict[str, Any] = {"file": str(path_b)}
    if selector_a:
        source_a["selector"] = selector_a
    if selector_b:
        source_b["selector"] = selector_b
    return {
        "name": "Federated clearance clashes",
        "mode": "clearance",
        "check_all": True,
        "clearance": clearance_m,
        "a": [source_a],
        "b": [source_b],
    }


def aabb_volume_m3(
    xmin: float,
    ymin: float,
    zmin: float,
    xmax: float,
    ymax: float,
    zmax: float,
) -> float:
    """Axis-aligned box volume in cubic metres (clamped at zero)."""

    dx = max(0.0, float(xmax) - float(xmin))
    dy = max(0.0, float(ymax) - float(ymin))
    dz = max(0.0, float(zmax) - float(zmin))
    return dx * dy * dz


def guid_include_selector(guids: Sequence[str]) -> str | None:
    """IfcOpenShell selector that includes only the given GlobalIds."""

    cleaned = [guid.strip() for guid in guids if guid and guid.strip()]
    if not cleaned:
        return None
    return ", ".join(f"#{guid}" for guid in cleaned)


@dataclass(frozen=True)
class ClashGeometryProbe:
    """Per-file geometry probe used before IfcClash tree build."""

    included_guids: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]

    @property
    def skipped_guids(self) -> tuple[str, ...]:
        return tuple(guid for guid, _reason in self.skipped)


def probe_clash_geometry(
    ifc_path: Path,
    *,
    min_aabb_volume_m3: float = DEFAULT_MIN_AABB_VOLUME_M3,
) -> ClashGeometryProbe:
    """Probe IfcProduct geometry; skip tiny boxes and geom-init failures.

    Per-element isolation: one ``AssertionError`` does not abort the probe.
    """

    import ifcopenshell
    import ifcopenshell.geom

    model = ifcopenshell.open(str(ifc_path))
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    included: list[str] = []
    skipped: list[tuple[str, str]] = []
    products = list(model.by_type("IfcProduct"))
    for product in products:
        guid = str(getattr(product, "GlobalId", "") or "")
        if not guid:
            continue
        if getattr(product, "Representation", None) is None:
            continue
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            verts = shape.geometry.verts
            xs = verts[0::3]
            ys = verts[1::3]
            zs = verts[2::3]
            if not xs:
                skipped.append((guid, "empty tessellation"))
                continue
            volume = aabb_volume_m3(min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))
            if volume < min_aabb_volume_m3:
                skipped.append((guid, f"aabb_volume={volume:.3e}m3 below {min_aabb_volume_m3}"))
                continue
            included.append(guid)
        except AssertionError as exc:
            detail = str(exc).strip() or "AssertionError"
            skipped.append((guid, f"geom init AssertionError: {detail}"))
        except Exception as exc:  # noqa: BLE001 — isolate one bad product
            skipped.append((guid, f"{type(exc).__name__}: {exc}"))
    if skipped:
        _LOGGER.warning(
            "Clash geometry probe skipped %s/%s products on %s",
            len(skipped),
            len(skipped) + len(included),
            ifc_path.name,
        )
    return ClashGeometryProbe(included_guids=tuple(included), skipped=tuple(skipped))


def _clash_type_label(clash: Mapping[str, Any], clash_set: Mapping[str, Any]) -> str:
    raw = str(clash.get("type", "") or clash_set.get("mode", "hard")).lower()
    if "clearance" in raw:
        return "clearance"
    if "collision" in raw:
        return "collision"
    return "hard"


def clash_results_from_sets(clash_sets: Sequence[Mapping[str, Any]]) -> list[ClashResult]:
    results: list[ClashResult] = []
    for clash_set_result in clash_sets:
        clashes = clash_set_result.get("clashes", {})
        if not isinstance(clashes, Mapping):
            continue
        for clash in clashes.values():
            if not isinstance(clash, Mapping):
                continue
            clash_type = _clash_type_label(clash, clash_set_result)
            label = "Clearance" if clash_type == "clearance" else "Hard clash"
            description = (
                f"{label} between {clash.get('a_name', '?')} and {clash.get('b_name', '?')}"
            )
            results.append(
                ClashResult(
                    element_a_guid=str(clash.get("a_global_id", "")),
                    element_b_guid=str(clash.get("b_global_id", "")),
                    clash_type=clash_type,
                    distance=float(clash.get("distance", 0.0) or 0.0),
                    description=description,
                )
            )
    return results


class IfcClashDetector:
    """Infrastructure adapter implementing ``ClashDetector`` port.

    Extra methods ``detect_between`` / ``detect_clearance_between`` reuse this
    adapter (same engine, no new DI token). Neither closes RT-003.
    """

    def __init__(
        self,
        *,
        skip_tiny_elements: bool = True,
        min_aabb_volume_m3: float = DEFAULT_MIN_AABB_VOLUME_M3,
    ) -> None:
        self._skip_tiny_elements = skip_tiny_elements
        self._min_aabb_volume_m3 = min_aabb_volume_m3

    def detect(self, ifc_path: Path) -> list[ClashResult]:
        if not ifc_path.exists():
            raise FileNotFoundError(f"IFC file not found: {ifc_path}")
        return self._guarded(lambda: self._run_clash_detection(ifc_path))

    def detect_between(self, path_a: Path, path_b: Path) -> list[ClashResult]:
        if not path_a.exists():
            raise FileNotFoundError(f"IFC file not found: {path_a}")
        if not path_b.exists():
            raise FileNotFoundError(f"IFC file not found: {path_b}")
        return self._guarded(lambda: self._run_federated_clash(path_a, path_b))

    def detect_clearance_between(
        self,
        path_a: Path,
        path_b: Path,
        *,
        clearance_m: float = 0.05,
    ) -> list[ClashResult]:
        if not path_a.exists():
            raise FileNotFoundError(f"IFC file not found: {path_a}")
        if not path_b.exists():
            raise FileNotFoundError(f"IFC file not found: {path_b}")
        return self._guarded(lambda: self._run_federated_clearance(path_a, path_b, clearance_m))

    def _guarded(self, runner: Callable[[], list[ClashResult]]) -> list[ClashResult]:
        try:
            return runner()
        except ImportError as exc:
            raise ClashCapabilityError(
                "skipped",
                f"IfcClash unavailable: {exc}",
            ) from exc
        except ClashCapabilityError:
            raise
        except Exception as exc:
            detail = str(exc).strip() or type(exc).__name__
            if isinstance(exc, AssertionError):
                detail = (
                    f"{detail}; IfcClash geometry init "
                    "(typical on tiny wall fixtures; not a silent pass)"
                )
            raise ClashCapabilityError(
                "failed",
                f"Clash detection failed: {detail}",
            ) from exc

    def _selector_for(self, ifc_path: Path) -> str | None:
        if not self._skip_tiny_elements:
            return None
        probe = probe_clash_geometry(ifc_path, min_aabb_volume_m3=self._min_aabb_volume_m3)
        if not probe.included_guids and probe.skipped:
            reasons = "; ".join(f"{guid}:{reason}" for guid, reason in probe.skipped[:8])
            raise ClashCapabilityError(
                "failed",
                "Clash geometry probe skipped all products "
                f"(tiny AABB or geom init); {reasons}",
            )
        if probe.skipped:
            return guid_include_selector(probe.included_guids)
        return None

    def _run_clash_detection(self, ifc_path: Path) -> list[ClashResult]:
        """Attempt IfcClash-based detection; raise ImportError if deps missing."""
        selector = self._selector_for(ifc_path)
        return self._run_clash_sets([self_clash_set(ifc_path, selector=selector)])

    def _run_federated_clash(self, path_a: Path, path_b: Path) -> list[ClashResult]:
        return self._run_clash_sets(
            [
                federated_clash_set(
                    path_a,
                    path_b,
                    selector_a=self._selector_for(path_a),
                    selector_b=self._selector_for(path_b),
                )
            ]
        )

    def _run_federated_clearance(
        self,
        path_a: Path,
        path_b: Path,
        clearance_m: float,
    ) -> list[ClashResult]:
        return self._run_clash_sets(
            [
                federated_clearance_clash_set(
                    path_a,
                    path_b,
                    clearance_m=clearance_m,
                    selector_a=self._selector_for(path_a),
                    selector_b=self._selector_for(path_b),
                )
            ]
        )

    def _run_clash_sets(self, clash_sets: list[dict[str, Any]]) -> list[ClashResult]:
        from ifcclash import ifcclash

        with tempfile.TemporaryDirectory(prefix="aerobim-ifcclash-") as temp_dir:
            settings = ifcclash.ClashSettings()
            settings.logger = logging.getLogger(__name__)
            settings.output = str(Path(temp_dir) / "clashes.json")

            clasher = ifcclash.Clasher(settings)
            clasher.clash_sets = clash_sets
            try:
                clasher.clash()
            except AssertionError:
                # Second chance: copy files, null tiny representations, retry once.
                retried = self._retry_clash_after_nulling_tiny(clasher, clash_sets, Path(temp_dir))
                if retried is not None:
                    return retried
                raise
            return clash_results_from_sets(clasher.clash_sets)

    def _retry_clash_after_nulling_tiny(
        self,
        clasher: Any,
        clash_sets: list[dict[str, Any]],
        temp_dir: Path,
    ) -> list[ClashResult] | None:
        if not self._skip_tiny_elements:
            return None
        rewritten: list[dict[str, Any]] = []
        for clash_set in clash_sets:
            clone = dict(clash_set)
            for key in ("a", "b"):
                sources = clone.get(key)
                if not isinstance(sources, list):
                    continue
                clone[key] = [self._null_tiny_source(source, temp_dir) for source in sources]
            rewritten.append(clone)
        clasher.clash_sets = rewritten
        clasher.clash()
        return clash_results_from_sets(clasher.clash_sets)

    def _null_tiny_source(self, source: Any, temp_dir: Path) -> dict[str, Any]:
        if not isinstance(source, Mapping):
            return {"file": str(source)}
        raw_file = source.get("file")
        if not raw_file:
            return dict(source)
        src_path = Path(str(raw_file))
        dest = temp_dir / f"filtered-{src_path.name}"
        shutil.copy2(src_path, dest)
        _null_skipped_representations(dest, self._min_aabb_volume_m3)
        out = dict(source)
        out["file"] = str(dest)
        out.pop("selector", None)
        return out


def _null_skipped_representations(ifc_path: Path, min_aabb_volume_m3: float) -> None:
    """Clear Representation on products the probe would skip (in-place)."""

    probe = probe_clash_geometry(ifc_path, min_aabb_volume_m3=min_aabb_volume_m3)
    skip = set(probe.skipped_guids)
    if not skip:
        return
    import ifcopenshell

    model = ifcopenshell.open(str(ifc_path))
    for product in model.by_type("IfcProduct"):
        guid = str(getattr(product, "GlobalId", "") or "")
        if guid in skip and getattr(product, "Representation", None) is not None:
            product.Representation = None
    model.write(str(ifc_path))
