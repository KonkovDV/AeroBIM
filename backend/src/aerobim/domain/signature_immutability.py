"""Detached signature envelope presence / integrity / roles (WP-03 foundation).

Honesty: this module never claims УКЭП legal validity, accredited CA/TSP trust,
or court-admissible qualified electronic signature verification. ``trust_chain_status``
is always ``not_verified``. Engineering checks cover fixture envelope structure,
content SHA-256 integrity, and required signer-role completeness only.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from aerobim.domain.models import CapabilityStatus

ENVELOPE_SCHEMA_V1 = "aerobim_detached_signature_envelope_v1"

CLAIM_BOUNDARY = (
    "Engineering only: detached envelope presence, content hash integrity, and "
    "signer role completeness on fixture envelopes. trust_chain_status is always "
    "not_verified (no accredited CA/TSP access). Does not claim УКЭП legal "
    "validity or qualified-signature verification."
)

TrustChainStatus = Literal["not_verified"]
OverallStatus = Literal["ok", "failed"]


@dataclass(frozen=True)
class SignerRoleRequirement:
    """Declared role that must appear among envelope signers."""

    role: str
    min_count: int = 1


@dataclass(frozen=True)
class SignatureSigner:
    """One signer entry inside a detached signature envelope."""

    role: str
    subject: str | None = None
    cert_not_before: str | None = None
    cert_not_after: str | None = None
    signature_alg: str | None = None
    signature_value: str | None = None


@dataclass(frozen=True)
class SignatureEnvelope:
    """Detached signature envelope (schema ``aerobim_detached_signature_envelope_v1``)."""

    schema: str
    content_sha256: str
    signers: tuple[SignatureSigner, ...] = ()
    signing_time: str | None = None
    content_path_hint: str | None = None
    content_hashes: tuple[tuple[str, str], ...] = ()
    package_hashes: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> SignatureEnvelope:
        raw_signers = payload.get("signers") or ()
        signers: list[SignatureSigner] = []
        if isinstance(raw_signers, Sequence) and not isinstance(raw_signers, (str, bytes)):
            for entry in raw_signers:
                if not isinstance(entry, Mapping):
                    continue
                role = str(entry.get("role") or "").strip()
                if not role:
                    continue
                signers.append(
                    SignatureSigner(
                        role=role,
                        subject=_optional_str(entry.get("subject")),
                        cert_not_before=_optional_str(entry.get("cert_not_before")),
                        cert_not_after=_optional_str(entry.get("cert_not_after")),
                        signature_alg=_optional_str(entry.get("signature_alg")),
                        signature_value=_optional_str(entry.get("signature_value")),
                    )
                )
        content_hashes = _parse_hash_map(payload.get("content_hashes"))
        package_hashes = _parse_hash_map(payload.get("package_hashes"))
        return cls(
            schema=str(payload.get("schema") or "").strip(),
            content_sha256=str(payload.get("content_sha256") or "").strip().lower(),
            signers=tuple(signers),
            signing_time=_optional_str(payload.get("signing_time")),
            content_path_hint=_optional_str(payload.get("content_path_hint")),
            content_hashes=content_hashes,
            package_hashes=package_hashes,
        )


@dataclass(frozen=True)
class SignatureAuditResult:
    """Outcome of an engineering signature-envelope audit (not legal УКЭП)."""

    structure_ok: bool
    integrity_ok: bool
    roles_complete: bool
    validity_window_ok: bool | None
    trust_chain_status: TrustChainStatus
    overall_status: OverallStatus
    claim_boundary: str
    reasons: tuple[str, ...] = ()

    def to_capability_status(self) -> CapabilityStatus:
        """Map audit onto report capability vocabulary (never pure legal OK)."""

        from aerobim.domain.models import CapabilityState, CapabilityStatus

        reason_bits = list(self.reasons)
        reason_bits.append(f"trust_chain_status={self.trust_chain_status}")
        reason_bits.append(self.claim_boundary)
        reason = "; ".join(reason_bits)
        if self.overall_status == "failed":
            return CapabilityStatus(CapabilityState.FAILED, reason)
        # Engineering checks may be ok, but trust chain is never verified →
        # prefer NOT_VERIFIED over a silent legal-looking OK for qualified_signature.
        return CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            (f"envelope presence/integrity/roles ok on fixture path; {reason}"),
        )


def content_sha256_hex(path: Path) -> str:
    """SHA-256 of file bytes (read-only; never rewrites content)."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def assess_signature_envelope(
    envelope: SignatureEnvelope | None,
    content_sha256: str,
    required_roles: Sequence[str] | Sequence[SignerRoleRequirement] = (),
    *,
    signing_time: datetime | str | None = None,
    observed_package_hashes: Mapping[str, str] | None = None,
) -> SignatureAuditResult:
    """Assess detached envelope structure, hash integrity, roles, and cert window.

    ``trust_chain_status`` is always ``not_verified``. ``overall_status`` is ``ok``
    only when structure, integrity, roles, signature field presence (no crypto verify),
    optional package/content hash binding, and validity window (when checked) pass.
    Never claims legal УКЭП validity.
    """

    reasons: list[str] = []
    structure_ok = True
    integrity_ok = True
    roles_complete = True
    signatures_present = True
    package_bind_ok = True
    validity_window_ok: bool | None = None

    if envelope is None:
        structure_ok = False
        integrity_ok = False
        roles_complete = False
        reasons.append("missing_envelope")
        return SignatureAuditResult(
            structure_ok=False,
            integrity_ok=False,
            roles_complete=False,
            validity_window_ok=None,
            trust_chain_status="not_verified",
            overall_status="failed",
            claim_boundary=CLAIM_BOUNDARY,
            reasons=tuple(reasons),
        )

    if envelope.schema != ENVELOPE_SCHEMA_V1:
        structure_ok = False
        reasons.append("missing_or_invalid_schema")
    if not envelope.content_sha256:
        structure_ok = False
        reasons.append("missing_content_sha256")
    if not envelope.signers:
        structure_ok = False
        reasons.append("missing_signers")

    expected = (content_sha256 or "").strip().lower()
    if not expected or envelope.content_sha256 != expected:
        integrity_ok = False
        reasons.append("content_sha256_mismatch")

    role_requirements = _normalize_role_requirements(required_roles)
    present_roles = [signer.role for signer in envelope.signers]
    for req in role_requirements:
        count = sum(1 for role in present_roles if role == req.role)
        if count < req.min_count:
            roles_complete = False
            reasons.append(f"missing_required_role:{req.role}")

    for signer in envelope.signers:
        if not signer.signature_alg:
            signatures_present = False
            reasons.append(f"missing_signature_alg:{signer.role}")
        if not signer.signature_value:
            signatures_present = False
            reasons.append(f"missing_signature_value:{signer.role}")

    declared_hashes = _merge_hash_maps(envelope.content_hashes, envelope.package_hashes)
    if declared_hashes:
        if not observed_package_hashes:
            package_bind_ok = False
            reasons.append("package_hashes_unbound:no_observed_hashes")
        else:
            observed = {
                str(key).strip(): str(value).strip().lower()
                for key, value in observed_package_hashes.items()
            }
            for path, expected in declared_hashes:
                actual = observed.get(path)
                if actual is None:
                    package_bind_ok = False
                    reasons.append(f"package_hash_missing:{path}")
                elif actual != expected:
                    package_bind_ok = False
                    reasons.append(f"package_hash_mismatch:{path}")

    check_time = _coerce_datetime(signing_time)
    if check_time is None and envelope.signing_time:
        check_time = _coerce_datetime(envelope.signing_time)
    if check_time is not None:
        validity_window_ok = True
        for signer in envelope.signers:
            not_before = _coerce_datetime(signer.cert_not_before)
            not_after = _coerce_datetime(signer.cert_not_after)
            if not_before is None or not_after is None:
                validity_window_ok = False
                reasons.append(f"missing_cert_window:{signer.role}")
                continue
            if check_time < not_before or check_time > not_after:
                validity_window_ok = False
                reasons.append(f"cert_outside_validity_window:{signer.role}")

    window_ok = True if validity_window_ok is None else validity_window_ok
    overall: OverallStatus = (
        "ok"
        if structure_ok
        and integrity_ok
        and roles_complete
        and signatures_present
        and package_bind_ok
        and window_ok
        else "failed"
    )
    if overall == "ok":
        reasons.append("engineering_envelope_checks_ok")
    reasons.append("trust_chain_not_verified")

    return SignatureAuditResult(
        structure_ok=structure_ok,
        integrity_ok=integrity_ok,
        roles_complete=roles_complete,
        validity_window_ok=validity_window_ok,
        trust_chain_status="not_verified",
        overall_status=overall,
        claim_boundary=CLAIM_BOUNDARY,
        reasons=tuple(reasons),
    )


def missing_envelope_result(*, reason: str = "missing_envelope") -> SignatureAuditResult:
    """Failed audit when a required envelope file is absent."""

    return SignatureAuditResult(
        structure_ok=False,
        integrity_ok=False,
        roles_complete=False,
        validity_window_ok=None,
        trust_chain_status="not_verified",
        overall_status="failed",
        claim_boundary=CLAIM_BOUNDARY,
        reasons=(reason, "trust_chain_not_verified"),
    )


def _normalize_role_requirements(
    required_roles: Sequence[str] | Sequence[SignerRoleRequirement],
) -> tuple[SignerRoleRequirement, ...]:
    out: list[SignerRoleRequirement] = []
    for item in required_roles:
        if isinstance(item, SignerRoleRequirement):
            role = item.role.strip()
            if role:
                out.append(SignerRoleRequirement(role=role, min_count=max(1, item.min_count)))
            continue
        role = str(item).strip()
        if role:
            out.append(SignerRoleRequirement(role=role, min_count=1))
    return tuple(out)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_hash_map(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        return ()
    out: list[tuple[str, str]] = []
    for raw_key, raw_val in value.items():
        key = str(raw_key).strip()
        digest = str(raw_val or "").strip().lower()
        if key and digest:
            out.append((key, digest))
    return tuple(out)


def _merge_hash_maps(
    *maps: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    merged: dict[str, str] = {}
    for mapping in maps:
        for path, digest in mapping:
            merged[path] = digest
    return tuple(merged.items())


def _coerce_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


__all__ = [
    "CLAIM_BOUNDARY",
    "ENVELOPE_SCHEMA_V1",
    "SignatureAuditResult",
    "SignatureEnvelope",
    "SignatureSigner",
    "SignerRoleRequirement",
    "assess_signature_envelope",
    "content_sha256_hex",
    "missing_envelope_result",
]
