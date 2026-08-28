"""Canonical sign-off / capability policy (SSOT).

Duplicated require_* flags across Settings, DI, and sign-off helpers historically
allowed profile drift (e.g. MEP NOT_VERIFIED green-pass under pilot wording).
All profile-aware blocking decisions must flow through ``SignOffCapabilityPolicy``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

SignOffProfileName = Literal[
    "development",
    "fixture",
    "samolet_pilot",
    "samolet_pilot_demo",
    "moscow_agr_2026",
    "production",
]

CUSTOMER_HARD_PROFILES: frozenset[str] = frozenset({"samolet_pilot", "production"})
HONEST_SCOPE_PROFILES: frozenset[str] = frozenset({"samolet_pilot_demo", "moscow_agr_2026"})
CLOSED_EGRESS_PROFILES: frozenset[str] = frozenset(
    {"samolet_pilot", "samolet_pilot_demo", "moscow_agr_2026", "production"}
)
_DEMO_REWRITE_STATES = frozenset(
    {
        CapabilityState.SKIPPED,
        CapabilityState.NOT_VERIFIED,
        CapabilityState.MISSING,
    }
)
_DEMO_CLASH_REASON = (
    "geometric clash is outside the demo-pilot boundary (RT-003 OPEN); not required and not faked"
)
_DEMO_MEP_REASON = (
    "MEP system clash is outside the demo-pilot boundary (RT-003 OPEN); not required and not faked"
)
_AGR_CLASH_REASON = (
    "geometric clash is outside Moscow AGR CIM scope (DGP-R-1/26); "
    "not required and not faked. RT-003 remains OPEN"
)
_AGR_MEP_REASON = (
    "federated MEP system clash is outside Moscow AGR CIM scope "
    "(федеративная проверка инженерных систем вне границы профиля АГР — "
    "не требуется и не подделывается); not required and not faked. "
    "RT-003 remains OPEN"
)

_PASS_BLOCKING_FAILED_FIELDS: tuple[str, ...] = (
    "clash",
    "ids",
    "ifc_validation",
    "unit_scale",
    "raster",
    "ifc_schema",
    "norm_rule_packs",
    "section_pairing",
    "calculation_match",
    "dwg_dxf",
    "mep_system_clash",
    "quantity",
    # LB/P-003: a FAILED extraction-integrity gate (render vs extract mismatch)
    # must never read as a clean pass; default NOT_VERIFIED stays non-blocking.
    "extraction_integrity",
    # WP-03: FAILED qualified_signature (missing required envelope / integrity)
    # blocks pass; default MISSING / NOT_VERIFIED stay non-blocking.
    "qualified_signature",
    # WP-05: FAILED package_completeness (missing mandatory section / pairing)
    # blocks pass; default SKIPPED stays non-blocking (soft opt-in).
    "package_completeness",
)

# Required capabilities: only OK is acceptable (Master Prompt §6).
_REQUIRED_NON_OK = frozenset(
    {
        CapabilityState.FAILED,
        CapabilityState.SKIPPED,
        CapabilityState.MISSING,
        CapabilityState.NOT_VERIFIED,
        CapabilityState.NOT_IMPLEMENTED,
    }
)


@dataclass(frozen=True)
class SignOffCapabilityPolicy:
    """Immutable policy object for deterministic sign-off gating."""

    profile: SignOffProfileName
    require_clash: bool = False
    clash_affects_pass: bool = False
    require_bsi_schema: bool = False
    require_mep_system_clash: bool = False
    enforce_object_acl: bool = False
    audit_fail_closed: bool = False

    def failed_capabilities_blocking_pass(
        self, capabilities: ReportCapabilities
    ) -> tuple[str, ...]:
        blocked: list[str] = []
        for name in _PASS_BLOCKING_FAILED_FIELDS:
            status = getattr(capabilities, name, None)
            if status is not None and status.status is CapabilityState.FAILED:
                blocked.append(name)
        return tuple(blocked)

    def required_capability_blocks_pass(self, capabilities: ReportCapabilities) -> tuple[str, ...]:
        """Profile-required capabilities that are not OK (SKIPPED/NOT_VERIFIED/…)."""

        blocked: list[str] = []
        if self.require_clash:
            clash = capabilities.clash
            if clash is None or clash.status in _REQUIRED_NON_OK:
                blocked.append("clash")
        if self.require_bsi_schema:
            schema = capabilities.ifc_schema
            if schema is None or schema.status in _REQUIRED_NON_OK:
                blocked.append("ifc_schema")
        if self.require_mep_system_clash:
            mep = capabilities.mep_system_clash
            if mep is None or mep.status in _REQUIRED_NON_OK:
                blocked.append("mep_system_clash")
        # RT-POST-06/07: pilot/production require verified unit_scale and do not
        # treat SKIPPED calculation/quantity as an implicit pass.
        if self.profile in CUSTOMER_HARD_PROFILES:
            for name in ("unit_scale", "calculation_match", "quantity"):
                status = getattr(capabilities, name, None)
                if status is None or status.status in _REQUIRED_NON_OK:
                    blocked.append(name)
            ids = getattr(capabilities, "ids", None)
            # RT-C3PO-001: None / NOT_VERIFIED / MISSING is silence, not a pass.
            # SKIPPED "not requested" stays the explicit opt-out (package without IDS).
            # Demo / AGR honest-scope profiles are not in this branch.
            if ids is None or ids.status in {
                CapabilityState.NOT_VERIFIED,
                CapabilityState.MISSING,
            }:
                blocked.append("ids")
            elif ids.status is CapabilityState.SKIPPED:
                reason = (ids.reason or "").lower()
                if "not requested" not in reason:
                    blocked.append("ids")
        return tuple(blocked)

    def mep_blocks_pass(self, capabilities: ReportCapabilities) -> bool:
        return "mep_system_clash" in self.required_capability_blocks_pass(capabilities)

    def summary_passed(
        self,
        *,
        error_count: int,
        capabilities: ReportCapabilities,
    ) -> bool:
        if error_count != 0:
            return False
        if self.failed_capabilities_blocking_pass(capabilities):
            return False
        if self.required_capability_blocks_pass(capabilities):
            return False
        calc = capabilities.calculation_match
        if calc is not None and calc.status is CapabilityState.NOT_VERIFIED:
            return False
        quantity = getattr(capabilities, "quantity", None)
        if quantity is not None and quantity.status is CapabilityState.NOT_VERIFIED:
            return False
        return True


_PROFILE_DEFAULTS: dict[SignOffProfileName, dict[str, bool]] = {
    "development": {
        "require_clash": False,
        "clash_affects_pass": False,
        "require_bsi_schema": False,
        "require_mep_system_clash": False,
        "enforce_object_acl": False,
        "audit_fail_closed": False,
    },
    "fixture": {
        "require_clash": False,
        "clash_affects_pass": False,
        "require_bsi_schema": False,
        "require_mep_system_clash": False,
        "enforce_object_acl": False,
        "audit_fail_closed": False,
    },
    "samolet_pilot": {
        "require_clash": True,
        "clash_affects_pass": True,
        "require_bsi_schema": True,
        "require_mep_system_clash": True,
        "enforce_object_acl": True,
        "audit_fail_closed": True,
    },
    "samolet_pilot_demo": {
        "require_clash": False,
        "clash_affects_pass": False,
        "require_bsi_schema": False,
        "require_mep_system_clash": False,
        "enforce_object_acl": True,
        "audit_fail_closed": True,
    },
    "moscow_agr_2026": {
        "require_clash": False,
        "clash_affects_pass": False,
        "require_bsi_schema": False,
        "require_mep_system_clash": False,
        "enforce_object_acl": True,
        "audit_fail_closed": True,
    },
    "production": {
        "require_clash": True,
        "clash_affects_pass": True,
        "require_bsi_schema": True,
        "require_mep_system_clash": True,
        "enforce_object_acl": True,
        "audit_fail_closed": True,
    },
}


def normalize_signoff_profile(raw: str | None) -> SignOffProfileName:
    value = (raw or "development").strip().lower()
    if value in {"dev", "development", "test"}:
        return "development"
    if value in {"fixture", "fixtures"}:
        return "fixture"
    if value in {"samolet", "samolet_pilot", "pilot"}:
        return "samolet_pilot"
    if value in {"samolet_pilot_demo", "pilot_demo"}:
        return "samolet_pilot_demo"
    if value in {"moscow_agr_2026", "moscow_agr", "agr_2026"}:
        return "moscow_agr_2026"
    if value in {"production", "prod"}:
        return "production"
    return "development"


def is_customer_hard_profile(name: str) -> bool:
    return name in CUSTOMER_HARD_PROFILES


def is_closed_egress_profile(name: str) -> bool:
    return name in CLOSED_EGRESS_PROFILES


def apply_demo_scope_honesty(
    capabilities: ReportCapabilities,
    *,
    profile: str | None = None,
) -> ReportCapabilities:
    """Stamp clash/MEP as SKIPPED out-of-scope on honest-scope contours.

    Does not rewrite OK/FAILED (a real engine result stays). Does not close RT-003.
    ``moscow_agr_2026`` cites AGR CIM scope, not demo convenience.
    """

    name = normalize_signoff_profile(profile) if profile else "samolet_pilot_demo"
    clash_reason = _AGR_CLASH_REASON if name == "moscow_agr_2026" else _DEMO_CLASH_REASON
    mep_reason = _AGR_MEP_REASON if name == "moscow_agr_2026" else _DEMO_MEP_REASON
    clash = capabilities.clash
    mep = capabilities.mep_system_clash
    if clash.status in _DEMO_REWRITE_STATES:
        clash = CapabilityStatus(CapabilityState.SKIPPED, clash_reason)
    if mep.status in _DEMO_REWRITE_STATES:
        mep = CapabilityStatus(CapabilityState.SKIPPED, mep_reason)
    return replace(capabilities, clash=clash, mep_system_clash=mep)


def build_signoff_policy(
    *,
    profile: str | None = None,
    require_clash: bool | None = None,
    clash_affects_pass: bool | None = None,
    require_bsi_schema: bool | None = None,
    require_mep_system_clash: bool | None = None,
    enforce_object_acl: bool | None = None,
    audit_fail_closed: bool | None = None,
) -> SignOffCapabilityPolicy:
    """Merge explicit overrides onto profile defaults.

    Soft profiles (``development`` / ``fixture``) allow explicit overrides.
    Hard customer profiles (``samolet_pilot`` / ``production``) always use
    profile defaults — weakening overrides are ignored (RT D03).
    ``samolet_pilot_demo`` / ``moscow_agr_2026`` are locked honest-scope
    contours: clash/MEP stay out of scope (not faked); ACL/audit stay on.
    Neither closes RT-003. ``moscow_agr_2026`` is not a customer-hard profile.
    """

    name = normalize_signoff_profile(profile)
    defaults = _PROFILE_DEFAULTS[name]
    hard = name in CUSTOMER_HARD_PROFILES or name in HONEST_SCOPE_PROFILES

    def _pick(key: str, override: bool | None) -> bool:
        if hard or override is None:
            return defaults[key]
        return override

    return SignOffCapabilityPolicy(
        profile=name,
        require_clash=_pick("require_clash", require_clash),
        clash_affects_pass=_pick("clash_affects_pass", clash_affects_pass),
        require_bsi_schema=_pick("require_bsi_schema", require_bsi_schema),
        require_mep_system_clash=_pick("require_mep_system_clash", require_mep_system_clash),
        enforce_object_acl=_pick("enforce_object_acl", enforce_object_acl),
        audit_fail_closed=_pick("audit_fail_closed", audit_fail_closed),
    )
