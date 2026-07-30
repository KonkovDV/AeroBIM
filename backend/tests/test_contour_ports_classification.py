"""Guard: every CONTOUR_PORTS name resolves to a declared symbol or is reserved.

Red-team "port fantasy" guard (TR-103 / attack A7 in
docs/tz/TZ_V3_RED_TEAM_2026_07_30.md): the contour architecture map must never
drift ahead of the code. A name may appear in CONTOUR_PORTS only if it is a
declared Protocol/class/value object in one of the modules below, or is listed
explicitly in RESERVED_PORTS.
"""

from __future__ import annotations

import importlib

from aerobim.domain.architecture import CONTOUR_PORTS, RESERVED_PORTS

# Modules that declare the port Protocols, wired orchestrators, and value
# objects referenced by the contour map.
_DECLARING_MODULES = (
    "aerobim.domain.ports",
    "aerobim.domain.tz_architecture_ports",
    "aerobim.domain.mep",
    "aerobim.domain.architecture",
    "aerobim.application.services.ids_assist_boundary",
    "aerobim.application.services.compliance_agent_orchestrator",
    "aerobim.application.services.agentic_review_orchestrator",
)


def _declared_symbols() -> set[str]:
    names: set[str] = set()
    for module_name in _DECLARING_MODULES:
        module = importlib.import_module(module_name)
        names.update(vars(module))
    return names


def _all_contour_port_names() -> set[str]:
    names: set[str] = set()
    for port_names in CONTOUR_PORTS.values():
        names.update(port_names)
    return names


def test_every_contour_port_is_declared_or_reserved() -> None:
    declared = _declared_symbols()
    unresolved = {
        name
        for name in _all_contour_port_names()
        if name not in declared and name not in RESERVED_PORTS
    }
    assert not unresolved, (
        f"CONTOUR_PORTS names neither declared nor reserved (port fantasy): {sorted(unresolved)}"
    )


def test_reserved_ports_are_subset_of_contour_ports() -> None:
    stray = RESERVED_PORTS - _all_contour_port_names()
    assert not stray, f"RESERVED_PORTS names absent from CONTOUR_PORTS: {sorted(stray)}"


def test_reserved_ports_are_not_already_declared() -> None:
    # Once a reserved name gains a real declaration it must leave RESERVED_PORTS.
    declared = _declared_symbols()
    leaked = {name for name in RESERVED_PORTS if name in declared}
    assert not leaked, f"RESERVED_PORTS names already declared -- remove them: {sorted(leaked)}"
