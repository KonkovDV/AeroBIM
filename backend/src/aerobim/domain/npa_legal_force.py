"""Legal-force qualification of TIM/CIM artefacts. Not legal advice.

Snapshot ``as_of=2026-08-14``. Encodes source hierarchy so IDS coverage, AGR
class-1 checks, EGRZ metadata, and MinStroy XSD *intake* cannot be promoted to
GrK art. 49 expertise, an AGR certificate, or a customer-signed EIR. No new port.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Final

AS_OF: Final = "2026-08-14"
DEFAULT_CONFIG_RELATIVE: Final = "samples/config/npa-instrument-register-2026-08-14.json"
CLAIM_BOUNDARY: Final = (
    "Legal-force labels for engineering honesty. Not a court opinion. "
    "Not statutory compliance of a customer package. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false)."
)

FORCE_FEDERAL_STATUTE: Final = "federal_statute"
FORCE_PP_RF: Final = "pp_rf"
FORCE_AGENCY_ORDER: Final = "agency_order"
FORCE_NTD_VOLUNTARY: Final = "ntd_voluntary"
FORCE_TERRITORIAL_NPA: Final = "territorial_npa"
FORCE_NOT_NPA: Final = "not_npa"
FORCE_DRAFT: Final = "draft_unverified"
LEGAL_FORCE_TIERS: Final[frozenset[str]] = frozenset(
    {
        FORCE_FEDERAL_STATUTE,
        FORCE_PP_RF,
        FORCE_AGENCY_ORDER,
        FORCE_NTD_VOLUNTARY,
        FORCE_TERRITORIAL_NPA,
        FORCE_NOT_NPA,
        FORCE_DRAFT,
    }
)
RT_CLOSE_KEYS: Final[tuple[str, ...]] = (
    "closes_rt001",
    "closes_rt002",
    "closes_rt003",
    "closes_rt002_customer_profile",
)

# PP 614 composition-of-electronic-documents item 7 — not Rules item 7 (GIS pointers).
PP614_FORMATS_CITATION: Final = (
    "PP RF 614 of 17.05.2024, composition of electronic documents item 7 "
    "subitems b/g/d: PDF/A; LandXML or open-spec terrain; IFC or open-spec CIM. "
    "Do not cite Rules item 7 (open GIS resource pointers) as the format list."
)

MINSTROY_CIM_COMPOSITION: Final[dict[str, Any]] = {
    "instrument_id": "MINSTROY-CIM-PD-GRAPHICS-DRAFT",
    "legal_force": FORCE_DRAFT,
    "regulation_gov_id": "155923",
    "orv": "negative_minec",
    "planned_window": "2026-03-01/2030-09-01",
    "in_force_on_as_of": False,
    "do_not_cite_as": "усиление с 01.03.2026",
}

PP878_DISAMBIGUATION: Final[dict[str, Any]] = {
    "egrz": {
        "instrument_id": "PP-RF-878-2017-07-24",
        "date": "2017-07-24",
        "subject": "egrz_rules",
        "public_fields": "metadata_not_remark_corpus",
    },
    "radioelectronics_trap": {
        "instrument_id": "PP-RF-878-2019-07-10",
        "date": "2019-07-10",
        "subject": "radioelectronics",
        "not": "egrz",
    },
}

EGRZ_INTAKE_LEGAL: Final[dict[str, Any]] = {
    "as_of": AS_OF,
    "product_function": "egrz_intake_precheck",
    "legal_force_of_cited_npa": FORCE_AGENCY_ORDER,
    "xsd_files_legal_force": FORCE_NOT_NPA,
    "cited_instrument_ids": ("MINSTROY-783-PR", "PP-RF-878-2017-07-24"),
    "substitutes_grk_art_49_expertise": False,
    "substitutes_egrz_remark_corpus": False,
    "substitutes_ukep_check": False,
    "closes_rt001": False,
    "closes_rt002": False,
    "closes_rt003": False,
    "claim_boundary": CLAIM_BOUNDARY,
}

AGR_EXCHANGE_LEGAL: Final[dict[str, Any]] = {
    "as_of": AS_OF,
    "product_function": "precheck_exchange_shape",
    "legal_force_of_cited_npa": FORCE_TERRITORIAL_NPA,
    "ids_zip_legal_force": FORCE_NOT_NPA,
    "territorial_scope": "moscow",
    "cited_instrument_ids": ("MOSCOW-17-PP", "DGP-R-1-26"),
    "substitutes_agr_certificate": False,
    "substitutes_grk_art_49_expertise": False,
    "substitutes_pp614_im_obligation": False,
    "substitutes_egrz_remark_corpus": False,
    "federal_im_obligation_created": False,
    "closes_rt002": False,
    "claim_boundary": CLAIM_BOUNDARY,
}

_IDS_COMMON: Final[dict[str, Any]] = {
    "legal_force": FORCE_NOT_NPA,
    "substitutes_grk_art_49_expertise": False,
    "substitutes_agr_certificate": False,
    "substitutes_egrz_remark_corpus": False,
    "substitutes_customer_eir": False,
    "closes_rt001": False,
    "closes_rt002": False,
    "closes_rt003": False,
}

IDS_PACK_LEGAL: Final[dict[str, dict[str, Any]]] = {
    "MOEXP-GAU-IDS": {
        **_IDS_COMMON,
        "instrument_id": "MOEXP-IDS-METHODOLOGY",
        "territorial_scope": "moscow_oblast",
        "cited_npa_ids": ("GRK-ART-49", "PP-RF-145"),
    },
    "MOSCOW-AGR-DGP-IDS": {
        **_IDS_COMMON,
        "instrument_id": "MOSCOW-AGR-IDS-METHODOLOGY",
        "territorial_scope": "moscow",
        "cited_npa_ids": ("MOSCOW-17-PP", "DGP-R-1-26"),
    },
    "SPBEXP-GAU-CGE-IDS": {
        **_IDS_COMMON,
        "instrument_id": "SPBEXP-IDS-METHODOLOGY",
        "territorial_scope": "spb",
        "cited_npa_ids": ("GRK-ART-49", "PP-RF-145"),
    },
}

_CIM_COMPOSITION_LINE = re.compile(
    r"(01\.03\.2026|1 марта 2026).{0,200}состав ЦИМ|состав ЦИМ.{0,200}(01\.03\.2026|1 марта 2026)",
    re.IGNORECASE,
)
_DRAFT_MARKERS = (
    "проект",
    "не подтвержд",
    "draft",
    "155923",
    "не цитировать",
    "не нпа",
    "not in force",
    FORCE_DRAFT,
)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


def agr_exchange_legal_payload() -> dict[str, Any]:
    payload = json_safe(AGR_EXCHANGE_LEGAL)
    if not isinstance(payload, dict):
        raise TypeError("AGR legal qualification must be an object")
    return payload


def overlay_egrz_intake(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Merge EGRZ intake legal-force fields. Refuse any RT-close=true."""

    for key in RT_CLOSE_KEYS:
        if payload.get(key) is True:
            raise ValueError(f"{key}=true is forbidden on EGRZ XML intake pre-check")
    out = dict(payload)
    out.update(json_safe(EGRZ_INTAKE_LEGAL))
    for key in RT_CLOSE_KEYS:
        if key in out:
            out[key] = False
    return out


def overlay_ids_pack(profile_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Merge jurisdiction legal-force fields. Refuse any RT-close=true."""

    try:
        legal = IDS_PACK_LEGAL[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown IDS profile_id {profile_id!r}") from exc
    for key in RT_CLOSE_KEYS:
        if payload.get(key) is True:
            raise ValueError(f"{key}=true is forbidden on jurisdiction IDS pack {profile_id}")
    out = dict(payload)
    out.update(json_safe(legal))
    for key in RT_CLOSE_KEYS:
        if key in out:
            out[key] = False
    return out


def cites_cim_composition_order_as_in_force(text: str) -> list[str]:
    """Return lines that treat the MinStroy CIM-composition *draft* as in force."""

    hits: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or not _CIM_COMPOSITION_LINE.search(line):
            continue
        folded = line.casefold()
        if any(marker.casefold() in folded for marker in _DRAFT_MARKERS):
            continue
        hits.append(line)
    return hits
