"""Data Classification Layer for the Hybrid AI routing contour (domain-pure).

Five sensitivity levels (brief §5). The engineering verdict is unaffected — this
layer only informs the fail-closed routing policy. Two hard rules:

1. **Never downgrade.** Combining classifications can only RAISE sensitivity
   (``most_restrictive``); nothing (least of all a model response or user input)
   may lower an object's class.
2. **Unknown is conservative.** An unrecognized object kind classifies as
   ``CONFIDENTIAL`` (never ``PUBLIC``); the policy engine treats a missing class
   as ``BLOCKED``.
"""

from __future__ import annotations

from enum import Enum


class DataClassification(Enum):
    """Sensitivity level of a single data object (request, IFC, crop, cache, ...)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"


# Ascending sensitivity; index is the rank used for "most restrictive" combination.
_ORDER: tuple[DataClassification, ...] = (
    DataClassification.PUBLIC,
    DataClassification.INTERNAL,
    DataClassification.CONFIDENTIAL,
    DataClassification.RESTRICTED,
    DataClassification.SECRET,
)


def rank(classification: DataClassification) -> int:
    return _ORDER.index(classification)


def most_restrictive(*classifications: DataClassification) -> DataClassification:
    """Return the highest-sensitivity class (never downgrades an aggregate)."""
    if not classifications:
        # Empty aggregate is not PUBLIC by default — stay conservative.
        return DataClassification.CONFIDENTIAL
    return max(classifications, key=rank)


# Conservative default map by object kind. Unknown kinds fall through to
# CONFIDENTIAL (never PUBLIC). A model must never move a kind into a lower row.
_KIND_DEFAULTS: dict[str, DataClassification] = {
    # PUBLIC
    "public_fixture": DataClassification.PUBLIC,
    "synthetic": DataClassification.PUBLIC,
    "public_standard": DataClassification.PUBLIC,
    "anonymized_demo": DataClassification.PUBLIC,
    "public_test_drawing": DataClassification.PUBLIC,
    # INTERNAL
    "internal_doc": DataClassification.INTERNAL,
    "anonymized_report": DataClassification.INTERNAL,
    "service_instruction": DataClassification.INTERNAL,
    # CONFIDENTIAL
    "ifc": DataClassification.CONFIDENTIAL,
    "drawing": DataClassification.CONFIDENTIAL,
    "calculation": DataClassification.CONFIDENTIAL,
    "specification": DataClassification.CONFIDENTIAL,
    "internal_norm": DataClassification.CONFIDENTIAL,
    "system_composition": DataClassification.CONFIDENTIAL,
    "bcf_real": DataClassification.CONFIDENTIAL,
    # RESTRICTED
    "customer_corpus": DataClassification.RESTRICTED,
    "samolet_data": DataClassification.RESTRICTED,
    "nda_document": DataClassification.RESTRICTED,
    "approved_norm_pack": DataClassification.RESTRICTED,
    "pii": DataClassification.RESTRICTED,
    "unmasked_report": DataClassification.RESTRICTED,
    # SECRET
    "secret": DataClassification.SECRET,
    "api_key": DataClassification.SECRET,
    "token": DataClassification.SECRET,
    "password": DataClassification.SECRET,
    "credential": DataClassification.SECRET,
    "security_config": DataClassification.SECRET,
    "internal_route": DataClassification.SECRET,
    "auth_log": DataClassification.SECRET,
}


def classify_object(kind: str) -> DataClassification:
    """Classify an object by its kind; unknown → CONFIDENTIAL (conservative)."""
    return _KIND_DEFAULTS.get((kind or "").strip().lower(), DataClassification.CONFIDENTIAL)


__all__ = [
    "DataClassification",
    "classify_object",
    "most_restrictive",
    "rank",
]
