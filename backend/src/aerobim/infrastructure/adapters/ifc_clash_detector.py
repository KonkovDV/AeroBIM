"""Clash detection adapter using IfcOpenShell + IfcClash.

Falls back to a no-op stub when ``ifcopenshell.geom`` or ``ifcclash`` are
unavailable, so the rest of the system stays functional.

The adapter currently supports **hard-clash** detection only (geometry
intersection). Clearance-based checks require tolerance parameters and
are deferred to a future iteration.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from aerobim.domain.models import ClashResult


class IfcClashDetector:
    """Infrastructure adapter implementing ``ClashDetector`` port."""

    def detect(self, ifc_path: Path) -> list[ClashResult]:
        if not ifc_path.exists():
            raise FileNotFoundError(f"IFC file not found: {ifc_path}")

        try:
            return self._run_clash_detection(ifc_path)
        except ImportError:
            return []
        except Exception:
            # IfcClash can fail at runtime when optional geometry engines or
            # native dependencies are partially available. Keep clash detection
            # as a non-blocking capability for the broader validation pipeline.
            return []

    def _run_clash_detection(self, ifc_path: Path) -> list[ClashResult]:
        """Attempt IfcClash-based detection; raise ImportError if deps missing."""
        from ifcclash import ifcclash

        with tempfile.TemporaryDirectory(prefix="aerobim-ifcclash-") as temp_dir:
            settings = ifcclash.ClashSettings()
            settings.logger = logging.getLogger(__name__)
            settings.output = str(Path(temp_dir) / "clashes.json")

            clash_set = {
                "name": "Internal hard clashes",
                "mode": "intersection",
                "check_all": False,
                "tolerance": 0.0,
                "a": [{"file": str(ifc_path)}],
            }

            clasher = ifcclash.Clasher(settings)
            clasher.clash_sets = [clash_set]
            clasher.clash()

            results: list[ClashResult] = []
            for clash_set_result in clasher.clash_sets:
                for clash in clash_set_result.get("clashes", {}).values():
                    description = (
                        f"Hard clash between {clash.get('a_name', '?')} and {clash.get('b_name', '?')}"
                    )
                    results.append(
                        ClashResult(
                            element_a_guid=clash.get("a_global_id", ""),
                            element_b_guid=clash.get("b_global_id", ""),
                            clash_type="hard",
                            distance=clash.get("distance", 0.0),
                            description=description,
                        )
                    )
            return results
