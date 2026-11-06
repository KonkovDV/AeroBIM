"""Interior discrepancy vocabulary for a design-studio pilot.

Twelve classes an architect and AeroBIM fill together. The catalog does not
run a check and does not write ``summary.passed``. A customer album stays
out of git. Didactic examples are not a measured result.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InteriorDiscrepancyClass:
    """One row of the abacus. ``code`` is stable; the example is not a finding."""

    code: str
    compares: str
    didactic_example: str


@dataclass(frozen=True, slots=True)
class InteriorPhaseGate:
    """A check between two stages of an interior method.

    ``needs_partner_export`` means the row cannot run on AeroBIM inputs alone.
    """

    code: str
    compares: str
    needs_partner_export: bool


# Didactic pairs from the collaboration note. Not a customer album.
INTERIOR_DISCREPANCY_CLASSES: tuple[InteriorDiscrepancyClass, ...] = (
    InteriorDiscrepancyClass(
        "D01",
        "schedule ↔ elevations",
        "Wall stone: 18.5 m² in the schedule, 17.0 m² on the elevations.",
    ),
    InteriorDiscrepancyClass(
        "D02",
        "plan ↔ schedule",
        "Sconce mark L-09 is on the plan and missing from the schedule.",
    ),
    InteriorDiscrepancyClass(
        "D03",
        "plan ↔ schedule",
        "14 downlights L-07 on the plan, 12 in the schedule.",
    ),
    InteriorDiscrepancyClass(
        "D04",
        "supplier card ↔ plan",
        "A wardrobe of 2400 mm is drawn into a 2350 mm niche.",
    ),
    InteriorDiscrepancyClass(
        "D05",
        "supplier card ↔ section",
        "A wardrobe 2700 mm high stands under a ceiling at 2650 mm.",
    ),
    InteriorDiscrepancyClass(
        "D06",
        "supplier card ↔ requirement",
        "A finish classed KM3 is specified on an escape route that asks for KM2.",
    ),
    InteriorDiscrepancyClass(
        "D07",
        "supplier card ↔ wet zone",
        "An IP20 luminaire is drawn in bathroom zone 1, which asks for at least IPX4.",
    ),
    InteriorDiscrepancyClass(
        "D08",
        "supplier card ↔ specification",
        "Floor tile has no R10 slip class where the specification asks for it.",
    ),
    InteriorDiscrepancyClass(
        "D09",
        "title block ↔ title block",
        "The schedule is on revision B; the sheet on site is revision C.",
    ),
    InteriorDiscrepancyClass(
        "D10",
        "equivalent ↔ specification",
        "The proposed equivalent has another class, size, or NCS colour.",
    ),
    InteriorDiscrepancyClass(
        "D11",
        "schedule ↔ supplier card",
        "Square metres were converted to packs with the wrong rounding.",
    ),
    InteriorDiscrepancyClass(
        "D12",
        "services drawing ↔ supplier card",
        "The water point is at 1100 mm; the mixer wants it at 1000 mm.",
    ),
)

INTERIOR_PHASE_GATES: tuple[InteriorPhaseGate, ...] = (
    InteriorPhaseGate("A", "concept areas and finish level ↔ investment schedule", True),
    InteriorPhaseGate("B", "illustrated schedule ↔ approved budget lines", True),
    InteriorPhaseGate(
        "C",
        "sheets ↔ schedule ↔ requirements: marks, counts, sizes, classes",
        False,
    ),
    InteriorPhaseGate("D", "site revision ↔ approved project", False),
    InteriorPhaseGate("E", "deliveries ↔ specification, and the handover dossier", True),
)


def writes_summary_passed() -> bool:
    """The abacus is a vocabulary. The deterministic core still owns the flag."""

    return False
