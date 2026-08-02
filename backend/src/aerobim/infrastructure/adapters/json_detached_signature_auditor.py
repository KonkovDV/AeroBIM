"""JSON detached signature envelope auditor (WP-03 foundation).

Loads ``*.sig.json`` next to the content file (or an explicit envelope path),
hashes content bytes read-only, and assesses the envelope via domain rules.
Never rewrites original content bytes. Never claims УКЭП legal validity —
``trust_chain_status`` stays ``not_verified``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path

from aerobim.domain.signature_immutability import (
    SignatureAuditResult,
    SignatureEnvelope,
    assess_signature_envelope,
    content_sha256_hex,
    missing_envelope_result,
)

_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")


class JsonDetachedSignatureAuditor:
    """Filesystem JSON adapter for ``DocumentSignatureAuditor``."""

    def audit(
        self,
        content_path: Path,
        *,
        envelope_path: Path | None = None,
        required_roles: Sequence[str] = (),
    ) -> SignatureAuditResult:
        resolved_envelope = (
            envelope_path
            if envelope_path is not None
            else content_path.with_suffix(content_path.suffix + ".sig.json")
        )
        if not resolved_envelope.is_file():
            return missing_envelope_result(reason="missing_envelope")

        try:
            payload = json.loads(resolved_envelope.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return SignatureAuditResult(
                structure_ok=False,
                integrity_ok=False,
                roles_complete=False,
                validity_window_ok=None,
                trust_chain_status="not_verified",
                overall_status="failed",
                claim_boundary=missing_envelope_result().claim_boundary,
                reasons=(f"envelope_unreadable:{exc}", "trust_chain_not_verified"),
            )

        if not isinstance(payload, dict):
            return SignatureAuditResult(
                structure_ok=False,
                integrity_ok=False,
                roles_complete=False,
                validity_window_ok=None,
                trust_chain_status="not_verified",
                overall_status="failed",
                claim_boundary=missing_envelope_result().claim_boundary,
                reasons=("envelope_not_object", "trust_chain_not_verified"),
            )

        # Read-only hash of original content — never rewrite content bytes.
        digest = content_sha256_hex(content_path)
        envelope = SignatureEnvelope.from_mapping(payload)
        observed_hashes = _observed_package_hashes(
            content_path,
            envelope,
            primary_digest=digest,
        )
        return assess_signature_envelope(
            envelope,
            digest,
            required_roles,
            signing_time=envelope.signing_time,
            observed_package_hashes=observed_hashes,
        )


def _observed_package_hashes(
    content_path: Path,
    envelope: SignatureEnvelope,
    *,
    primary_digest: str,
) -> dict[str, str] | None:
    """Build observed hash map when envelope declares package/content bindings.

    Paths are jailed under ``content_path.parent`` — absolute paths and ``..``
    traversal outside the content directory are ignored (no out-of-jail reads).
    """

    declared = {path: digest for path, digest in envelope.content_hashes}
    declared.update({path: digest for path, digest in envelope.package_hashes})
    if not declared:
        return None
    observed: dict[str, str] = {}
    base_dir = content_path.parent.resolve()
    for path, _expected in declared.items():
        if Path(path).is_absolute() or _DRIVE_ABS.match(path) or path.startswith("\\\\"):
            continue
        try:
            candidate = (base_dir / path).resolve()
        except OSError:
            continue
        if not candidate.is_relative_to(base_dir):
            continue
        if candidate.is_file():
            observed[path] = content_sha256_hex(candidate)
    # Always include the audited content under its basename when listed or implied.
    observed.setdefault(content_path.name, primary_digest)
    if envelope.content_path_hint:
        observed.setdefault(envelope.content_path_hint.strip(), primary_digest)
    return observed
