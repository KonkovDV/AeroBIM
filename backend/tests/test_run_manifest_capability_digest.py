"""RT-EI-04 guard: the reproducibility capability digest must exactly mirror the
pass-blocking capability set, and every digest name must be a real
ReportCapabilities field (phantom names are silently dropped by getattr --
that is how quantity/raster/ifc_schema fell out of the digest unnoticed).
"""

from __future__ import annotations

from dataclasses import fields

from aerobim.application.services.capability_policy import _PASS_BLOCKING_FAILED_FIELDS
from aerobim.domain.models import ReportCapabilities
from aerobim.domain.run_manifest import _CAPABILITY_FIELDS, capability_digest


class _ReportStub:
    summary = None
    issues: tuple = ()

    def __init__(self) -> None:
        self.capabilities = ReportCapabilities()


def test_digest_fields_mirror_pass_blocking_set() -> None:
    assert set(_CAPABILITY_FIELDS) == set(_PASS_BLOCKING_FAILED_FIELDS), (
        "run_manifest._CAPABILITY_FIELDS drifted from "
        "capability_policy._PASS_BLOCKING_FAILED_FIELDS -- update both together "
        "and consciously refresh the golden reproducibility hash"
    )


def test_every_digest_name_is_a_real_capability_field() -> None:
    real = {f.name for f in fields(ReportCapabilities)}
    phantom = sorted(set(_CAPABILITY_FIELDS) - real)
    assert not phantom, f"phantom capability names silently dropped by getattr: {phantom}"


def test_digest_emits_every_field_no_silent_drops() -> None:
    digest = capability_digest(_ReportStub())
    assert set(digest) == set(_CAPABILITY_FIELDS)
    assert all(isinstance(v, str) and v for v in digest.values())
