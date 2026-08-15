"""Clash detection adapter using IfcOpenShell + IfcClash.

Raises ``ClashCapabilityError`` when the optional geometry stack is missing or
fails, so callers can record an explicit capability status instead of treating
silent empty results as a clean model.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.models import ClashResult


def self_clash_set(ifc_path: Path) -> dict[str, Any]:
    """Single-file package: self-clash within set A."""
    return {
        "name": "Internal hard clashes",
        "mode": "intersection",
        "check_all": True,
        "tolerance": 0.0,
        "a": [{"file": str(ifc_path)}],
    }


def federated_clash_set(path_a: Path, path_b: Path) -> dict[str, Any]:
    """Two-file intersection (architecture vs MEP, etc.). Not system-aware."""
    return {
        "name": "Federated hard clashes",
        "mode": "intersection",
        "check_all": True,
        "tolerance": 0.0,
        "a": [{"file": str(path_a)}],
        "b": [{"file": str(path_b)}],
    }


def federated_clearance_clash_set(
    path_a: Path,
    path_b: Path,
    *,
    clearance_m: float,
) -> dict[str, Any]:
    """Two-file soft clearance (IfcClash mode=clearance). Not MEP system-aware."""
    if clearance_m <= 0:
        raise ValueError("clearance_m must be > 0")
    return {
        "name": "Federated clearance clashes",
        "mode": "clearance",
        "check_all": True,
        "clearance": clearance_m,
        "a": [{"file": str(path_a)}],
        "b": [{"file": str(path_b)}],
    }


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

    def _run_clash_detection(self, ifc_path: Path) -> list[ClashResult]:
        """Attempt IfcClash-based detection; raise ImportError if deps missing."""
        return self._run_clash_sets([self_clash_set(ifc_path)])

    def _run_federated_clash(self, path_a: Path, path_b: Path) -> list[ClashResult]:
        return self._run_clash_sets([federated_clash_set(path_a, path_b)])

    def _run_federated_clearance(
        self,
        path_a: Path,
        path_b: Path,
        clearance_m: float,
    ) -> list[ClashResult]:
        return self._run_clash_sets(
            [federated_clearance_clash_set(path_a, path_b, clearance_m=clearance_m)]
        )

    def _run_clash_sets(self, clash_sets: list[dict[str, Any]]) -> list[ClashResult]:
        from ifcclash import ifcclash

        with tempfile.TemporaryDirectory(prefix="aerobim-ifcclash-") as temp_dir:
            settings = ifcclash.ClashSettings()
            settings.logger = logging.getLogger(__name__)
            settings.output = str(Path(temp_dir) / "clashes.json")

            clasher = ifcclash.Clasher(settings)
            clasher.clash_sets = clash_sets
            clasher.clash()
            return clash_results_from_sets(clasher.clash_sets)
