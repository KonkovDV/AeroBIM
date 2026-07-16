"""Domain vocabulary for deterministic PD/RD section pairing.

This module is intentionally free of infrastructure dependencies (Clean
Architecture: Domain must not import Application or Infrastructure). It provides
three deterministic building blocks used by ``SectionDiffAnalyzer`` adapters and
by the analyze use case:

* a **canonical discipline registry** that folds RU/EN drawing-set marks
  (``АР``/``AR``, ``КЖ``/``KZH`` …) onto a single canonical code so a PD and RD
  section labelled in different languages are not reported as a discipline
  mismatch;
* a **canonical key registry** that folds RU/EN attribute aliases onto a single
  canonical key so ``защитный.слой`` (RD) and ``rebar.cover`` (PD) pair up
  without fuzzy or model-generated matching;
* a deterministic Cyrillic→Latin ``slugify`` so rule identifiers stay stable and
  URL/BCF-safe even when the source section uses Cyrillic codes.

Everything here is a *scaffold* vocabulary seeded for the synthetic residential
demo. It is not a claim of full SP/GOST canonical-key coverage — a customer
canonical-key freeze remains a pilot blocker (see
``docs/section-pairing/README.md``). Unknown disciplines and keys are handled
honestly: they are still compared, but reported as ``recognized=False`` so the
capability status cannot silently look complete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from aerobim.domain.models import ValidationIssue

__all__ = [
    "DisciplineInfo",
    "CanonicalKeyResult",
    "SectionPairingReport",
    "canonicalize_discipline",
    "canonicalize_key",
    "normalize_key",
    "slugify",
    "transliterate",
    "known_discipline_codes",
]

# --------------------------------------------------------------------------- #
# Cyrillic → Latin transliteration (deterministic, GOST 7.79 System B-ish).
# Only used to build stable Latin slugs for rule identifiers; it is never used
# for value comparison.
# --------------------------------------------------------------------------- #
_CYRILLIC_TO_LATIN: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "cz", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def transliterate(raw: str) -> str:
    """Return a deterministic Latin transliteration of ``raw``.

    Latin characters pass through unchanged; Cyrillic characters are mapped
    case-insensitively (the caller upper-cases where needed).
    """
    return "".join(_CYRILLIC_TO_LATIN.get(ch, ch) for ch in raw.casefold())


def slugify(raw: str) -> str:
    """Return a stable, upper-case, Latin, ``[A-Z0-9-]`` slug for ``raw``.

    Cyrillic is transliterated first so RU section codes/keys yield readable,
    unique identifiers instead of collapsing to a single placeholder.
    """
    slug = re.sub(r"[^A-Za-z0-9]+", "-", transliterate(raw).upper()).strip("-")
    return slug[:96] or "VALUE"


# --------------------------------------------------------------------------- #
# Discipline registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class DisciplineInfo:
    """Canonical discipline resolution outcome."""

    code: str
    label: str
    recognized: bool
    raw: str


# canonical_code -> (human label, tuple of aliases in any case / language).
# Aliases are matched after casefolding + separator normalisation.
_DISCIPLINE_DEFS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("AR", "Architecture (АР)", ("ar", "ар", "арх", "arch", "architecture", "архитектурные")),
    ("KZH", "Reinforced concrete structures (КЖ)",
     ("kzh", "кж", "кж0", "rc", "reinforced-concrete", "жб", "жбк")),
    ("KM", "Metal structures (КМ)", ("km", "км", "metal", "steel", "металлоконструкции")),
    ("KR", "Structures, general (КР)", ("kr", "кр", "structural", "structures", "конструкции")),
    ("GP", "General layout / site (ГП)",
     ("gp", "гп", "general-plan", "site", "генплан", "sp", "сп-genplan")),
    ("OV", "Heating & ventilation (ОВ)",
     ("ov", "ов", "hvac", "heating", "ventilation", "отопление", "овик")),
    ("VK", "Water supply & sewerage (ВК)",
     ("vk", "вк", "plumbing", "water", "водоснабжение", "канализация")),
    ("EOM", "Electrical, power (ЭОМ)",
     ("eom", "эом", "эм", "электрика", "electrical", "power", "эс")),
    ("SS", "Low-current / communications (СС)",
     ("ss", "сс", "low-current", "слаботочные", "communications")),
    ("PS", "Fire alarm (ПС/ОПС)", ("ps", "пс", "ops", "опс", "fire-alarm")),
    ("TKH", "Technology (ТХ)", ("tkh", "тх", "tx", "technology", "технология")),
    ("PB", "Fire safety (ПБ)",
     ("pb", "пб", "fire-safety", "пожарная-безопасность", "мпб")),
    ("OOS", "Environmental protection (ООС)",
     ("oos", "оос", "environmental", "экология")),
    ("PZ", "Explanatory note (ПЗ)", ("pz", "пз", "explanatory-note")),
)


def _build_discipline_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for code, label, aliases in _DISCIPLINE_DEFS:
        # canonical code is always a self-alias
        for alias in (code, *aliases):
            index[_fold(alias)] = (code, label)
    return index


def _fold(raw: str) -> str:
    """Casefold and collapse separators to a single dot for alias lookup."""
    folded = raw.strip().casefold()
    folded = re.sub(r"[\s_./:\\-]+", ".", folded)
    return folded.strip(".")


def known_discipline_codes() -> tuple[str, ...]:
    """Return the tuple of canonical discipline codes, sorted and stable."""
    return tuple(code for code, _label, _aliases in _DISCIPLINE_DEFS)


_DISCIPLINE_INDEX = _build_discipline_index()


def canonicalize_discipline(raw: str) -> DisciplineInfo:
    """Resolve a raw discipline token to its canonical code.

    Unknown disciplines are echoed back (upper-cased, transliterated) with
    ``recognized=False`` so they are still comparable but never look complete.
    """
    hit = _DISCIPLINE_INDEX.get(_fold(raw))
    if hit is not None:
        code, label = hit
        return DisciplineInfo(code=code, label=label, recognized=True, raw=raw)
    fallback = slugify(raw)
    return DisciplineInfo(
        code=fallback,
        label=f"Unrecognized discipline ({raw})",
        recognized=False,
        raw=raw,
    )


# --------------------------------------------------------------------------- #
# Canonical key registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CanonicalKeyResult:
    """Canonical key resolution outcome for a single section value key."""

    canonical: str
    recognized: bool
    raw: str


def normalize_key(raw: str) -> str:
    """Normalise a raw key: casefold and collapse separators to a single dot."""
    normalized = raw.strip().casefold()
    normalized = re.sub(r"[\s_./:\\-]+", ".", normalized)
    return normalized.strip(".")


# Keys shared across every discipline. canonical -> aliases.
_COMMON_KEY_DEFS: dict[str, tuple[str, ...]] = {
    "building.height": ("высота.здания", "building.height"),
    "floor.count": ("этажность", "количество.этажей", "floors", "floor.count", "number.of.storeys"),
    "building.levels.above": ("количество.надземных.этажей", "storeys.above.ground"),
}

# Discipline-scoped keys. discipline_code -> {canonical: aliases}.
_DISCIPLINE_KEY_DEFS: dict[str, dict[str, tuple[str, ...]]] = {
    "AR": {
        "apartment.area.total": (
            "площадь.квартиры", "room.area.total", "площадь.помещения", "apartment.area.total",
        ),
        "wall.external.thickness": ("толщина.наружной.стены", "wall.external.thickness"),
        "door.clear.width": (
            "ширина.двери.в.свету", "ширина.проема.двери", "door.clear.width",
        ),
        "facade.material": ("материал.фасада", "facade.material"),
        "railing.height": ("высота.ограждения", "высота.перил", "railing.height"),
        "ceiling.height": ("высота.потолка", "ceiling.height"),
        "window.area": ("площадь.окна", "window.area"),
    },
    "KZH": {
        "concrete.class": ("класс.бетона", "concrete.class", "concrete.grade"),
        "rebar.cover": (
            "защитный.слой", "защитный.слой.бетона", "rebar.cover", "concrete.cover",
        ),
        "rebar.grade": ("класс.арматуры", "rebar.grade"),
        "slab.thickness": ("толщина.плиты", "slab.thickness"),
        "foundation.depth": (
            "глубина.заложения.фундамента", "глубина.фундамента", "foundation.depth",
        ),
        "column.section": ("сечение.колонны", "column.section"),
    },
    "KM": {
        "steel.grade": ("марка.стали", "steel.grade"),
        "beam.section": ("сечение.балки", "beam.section"),
    },
    "OV": {
        "air.exchange.rate": ("кратность.воздухообмена", "air.exchange.rate"),
        "supply.airflow": ("расход.приточного.воздуха", "supply.airflow"),
    },
    "VK": {
        "water.pressure": ("давление.воды", "water.pressure"),
        "pipe.diameter": ("диаметр.трубы", "pipe.diameter"),
    },
    "EOM": {
        "power.rated": ("установленная.мощность", "power.rated"),
        "cable.section": ("сечение.кабеля", "cable.section"),
    },
}


def _build_key_index() -> dict[str, dict[str, str]]:
    """Build discipline_code -> {normalized_alias: canonical}."""
    index: dict[str, dict[str, str]] = {}
    common: dict[str, str] = {}
    for canonical, aliases in _COMMON_KEY_DEFS.items():
        for alias in (canonical, *aliases):
            common[normalize_key(alias)] = canonical
    index["*"] = common
    for discipline, defs in _DISCIPLINE_KEY_DEFS.items():
        scoped: dict[str, str] = {}
        for canonical, aliases in defs.items():
            for alias in (canonical, *aliases):
                scoped[normalize_key(alias)] = canonical
        index[discipline] = scoped
    return index


_KEY_INDEX = _build_key_index()


def canonicalize_key(raw: str, discipline_code: str) -> CanonicalKeyResult:
    """Resolve a raw section-value key to its canonical form.

    Resolution order: discipline-scoped aliases, then cross-discipline common
    aliases. On a miss, the normalised key is returned with ``recognized=False``
    (still deterministic and comparable, but honestly flagged as unmapped).
    """
    normalized = normalize_key(raw)
    scoped = _KEY_INDEX.get(discipline_code.upper())
    if scoped is not None:
        canonical = scoped.get(normalized)
        if canonical is not None:
            return CanonicalKeyResult(canonical=canonical, recognized=True, raw=raw)
    common = _KEY_INDEX.get("*", {})
    canonical = common.get(normalized)
    if canonical is not None:
        return CanonicalKeyResult(canonical=canonical, recognized=True, raw=raw)
    return CanonicalKeyResult(canonical=normalized, recognized=False, raw=raw)


# --------------------------------------------------------------------------- #
# Pairing report value object
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SectionPairingReport:
    """Deterministic outcome of one PD/RD section comparison.

    Carries the findings plus honest coverage metadata so the capability status
    can report *what was recognised* without inflating it into an accuracy claim.
    """

    issues: tuple[ValidationIssue, ...]
    discipline: DisciplineInfo
    section_code: str
    pd_document_id: str
    rd_document_id: str
    pd_key_count: int
    recognized_key_count: int
    unrecognized_keys: tuple[str, ...] = field(default_factory=tuple)

    @property
    def coverage_ratio(self) -> float:
        if self.pd_key_count == 0:
            return 0.0
        return self.recognized_key_count / self.pd_key_count

    def capability_reason(self, pd_name: str, rd_name: str) -> str:
        """Build a deterministic, honest capability reason string."""
        discipline_state = "recognized" if self.discipline.recognized else "unrecognized"
        return (
            f"paired {self.discipline.code} [{discipline_state}] "
            f"{pd_name} -> {rd_name}; "
            f"canonical-key coverage={self.recognized_key_count}/{self.pd_key_count}; "
            f"findings={len(self.issues)}"
        )
