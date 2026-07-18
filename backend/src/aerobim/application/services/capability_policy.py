"""Canonical sign-off / capability policy (SSOT).

Duplicated require_* flags across Settings, DI, and sign-off helpers historically
allowed profile drift (e.g. MEP NOT_VERIFIED green-pass under pilot wording).
All profile-aware blocking decisions must flow through ``SignOffCapabilityPolicy``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aerobim.domain.models import CapabilityState, ReportCapabilities

SignOffProfileName = Literal["development", "fixture", "samolet_pilot", "production"]

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
    if value in {"production", "prod"}:
        return "production"
    return "development"


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
    """Merge explicit overrides onto profile defaults (explicit wins)."""

    name = normalize_signoff_profile(profile)
    defaults = _PROFILE_DEFAULTS[name]
    return SignOffCapabilityPolicy(
        profile=name,
        require_clash=defaults["require_clash"] if require_clash is None else require_clash,
        clash_affects_pass=(
            defaults["clash_affects_pass"] if clash_affects_pass is None else clash_affects_pass
        ),
        require_bsi_schema=(
            defaults["require_bsi_schema"] if require_bsi_schema is None else require_bsi_schema
        ),
        require_mep_system_clash=(
            defaults["require_mep_system_clash"]
            if require_mep_system_clash is None
            else require_mep_system_clash
        ),
        enforce_object_acl=(
            defaults["enforce_object_acl"] if enforce_object_acl is None else enforce_object_acl
        ),
        audit_fail_closed=(
            defaults["audit_fail_closed"] if audit_fail_closed is None else audit_fail_closed
        ),
    )
