"""SystemClashPort — IFC system-aware clash when scope memo + flag present.

MEP-CLASH-001 remains open until customer federated IFC + signed clearance matrix.
Default: UnconfiguredSystemClash. This adapter is opt-in via settings.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aerobim.domain.tz_architecture_ports import SpatialFinding


class IfcSystemAwareClash:
    """Probe IfcSystem assignments + generic pairwise proximity (clearance scaffold).

    Without ``scope_memo_ref`` or systems in the model, fails closed — never empty-as-OK.
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        scope_memo_ref: str | None = None,
        default_clearance_mm: float = 50.0,
    ) -> None:
        self._enabled = enabled
        self._scope_memo_ref = (scope_memo_ref or "").strip() or None
        self._default_clearance_mm = default_clearance_mm

    def detect(
        self,
        model_path: Path,
        *,
        clearance_matrix: Mapping[tuple[str, str], float] | None = None,
    ) -> list[SpatialFinding]:
        if not self._enabled:
            raise RuntimeError(
                "MEP system-aware clash disabled (AEROBIM_MEP_SYSTEM_CLASH_ENABLED=false); "
                "MEP-CLASH-001"
            )
        if not self._scope_memo_ref:
            raise RuntimeError(
                "MEP system-aware clash requires AEROBIM_MEP_SCOPE_MEMO_REF "
                "(signed scope memo); MEP-CLASH-001"
            )
        if not model_path.exists():
            raise FileNotFoundError(model_path)

        try:
            import ifcopenshell
        except ModuleNotFoundError as exc:
            raise RuntimeError("ifcopenshell required for system-aware clash") from exc

        try:
            model = ifcopenshell.open(str(model_path))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"IFC open failed for system clash: {exc}") from exc

        systems = list(model.by_type("IfcSystem"))
        if not systems:
            raise RuntimeError(
                "No IfcSystem entities in model — federated MEP pack required "
                "(MEP-CLASH-001)"
            )

        # Scaffold: emit advisory routing findings for distinct system pairs (no geometry OK).
        findings: list[SpatialFinding] = []
        matrix = clearance_matrix or {}
        for index, system in enumerate(systems[:20]):
            system_id = str(getattr(system, "Name", None) or getattr(system, "GlobalId", index))
            peer = systems[(index + 1) % len(systems)]
            peer_id = str(getattr(peer, "Name", None) or getattr(peer, "GlobalId", index + 1))
            if system_id == peer_id:
                continue
            clearance = matrix.get((system_id, peer_id)) or matrix.get((peer_id, system_id))
            findings.append(
                SpatialFinding(
                    finding_id=f"mep-sys-{index}",
                    system_a=system_id,
                    system_b=peer_id,
                    element_a_guid=str(getattr(system, "GlobalId", "")),
                    element_b_guid=str(getattr(peer, "GlobalId", "")),
                    message=(
                        f"System pair advisory probe (scope={self._scope_memo_ref}); "
                        f"clearance_mm="
                        f"{clearance if clearance is not None else self._default_clearance_mm}; "
                        "geometry intersection not claimed — Solibri-class core "
                        "remains generic ClashDetector"
                    ),
                    clash_kind="clearance",
                    clearance_mm=(
                        float(clearance)
                        if clearance is not None
                        else self._default_clearance_mm
                    ),
                )
            )
        return findings
